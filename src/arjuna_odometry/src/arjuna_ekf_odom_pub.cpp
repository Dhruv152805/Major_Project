/*
 * Arjuna Optimized EKF Odometry Publisher
 * 
 * Fuses motor encoder ticks to publish wheel odometry (for standard EKF input).
 * Supports runtime parameter configuration for wheel radius, wheel base, tick scaling, etc.
 *
 * MODIFIED: added wheel-slip detection with dynamic covariance scaling.
 * When the computed per-cycle speed exceeds what the robot can physically
 * achieve, the wheels are almost certainly slipping rather than reporting
 * real motion (e.g. transitioning onto/off turf sections of the arena).
 * In that case, published odometry covariance is inflated so the EKF
 * (robot_localization) automatically leans more on the IMU for that
 * update instead of trusting bad wheel data at full confidence.
 * 
 * Target path: arjuna_odometry/src/arjuna_ekf_odom_pub.cpp
 */

#include <memory>
#include <cmath>
#include <mutex>
#include <algorithm>
#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/int64.hpp"
#include "nav_msgs/msg/odometry.hpp"
#include "geometry_msgs/msg/pose_stamped.hpp"
#include "tf2/LinearMath/Quaternion.h"
#include "tf2_ros/transform_broadcaster.h"
#include "geometry_msgs/msg/transform_stamped.hpp"
#include "rcl_interfaces/msg/set_parameters_result.hpp"

class ArjunaEKFOdomPublisher : public rclcpp::Node
{
public:
    ArjunaEKFOdomPublisher() : Node("arjuna_ekf_odom_pub")
    {
        // Declare parameters with default settings for the NEW Arjuna robot
        this->declare_parameter("publish_tf", false); // Default to false when EKF is active
        this->declare_parameter("wheel_radius", 0.04); // 4 cm / 80 mm diameter rubber wheels
        this->declare_parameter("wheel_base", 0.30);   // 30 cm track width on new Arjuna
        this->declare_parameter("ticks_per_revolution", 4096.0); // STS 12-bit encoder resolution
        this->declare_parameter("tick_scaling", 2.5);  // Divisor factor from new motor node
        this->declare_parameter("initial_x", 0.0);
        this->declare_parameter("initial_y", 0.0);
        this->declare_parameter("initial_theta", 0.0);
        this->declare_parameter("publish_rate", 30.0);
        this->declare_parameter("odom_frame", "odom");
        this->declare_parameter("base_frame", "base_footprint");
        this->declare_parameter("max_plausible_speed", 0.75); // m/s - slightly above rated 0.7 m/s top speed.
                                                                // Used for wheel-slip detection: a computed
                                                                // speed above this is physically implausible
                                                                // and almost certainly means slip, not real motion.

        // Load parameters
        publish_tf_ = this->get_parameter("publish_tf").as_bool();
        wheel_radius_ = this->get_parameter("wheel_radius").as_double();
        wheel_base_ = this->get_parameter("wheel_base").as_double();
        ticks_per_revolution_ = this->get_parameter("ticks_per_revolution").as_double();
        tick_scaling_ = this->get_parameter("tick_scaling").as_double();
        robot_x_ = this->get_parameter("initial_x").as_double();
        robot_y_ = this->get_parameter("initial_y").as_double();
        robot_theta_ = this->get_parameter("initial_theta").as_double();
        publish_rate_ = this->get_parameter("publish_rate").as_double();
        odom_frame_ = this->get_parameter("odom_frame").as_string();
        base_frame_ = this->get_parameter("base_frame").as_string();
        max_plausible_speed_ = this->get_parameter("max_plausible_speed").as_double();

        // Calculate initial ticks_per_meter
        calculate_ticks_per_meter();

        // Initialize state variables
        lastCountL_ = 0;
        lastCountR_ = 0;
        accumulated_left_ticks_ = 0;
        accumulated_right_ticks_ = 0;
        timer_last_left_ticks_ = 0;
        timer_last_right_ticks_ = 0;
        first_left_received_ = true;
        first_right_received_ = true;
        
        linear_velocity_ = 0.0;
        angular_velocity_ = 0.0;
        odom_covariance_scale_ = 1.0; // 1.0 = normal trust, >1.0 = degraded trust (slip detected)
        last_time_ = this->now();

        // Setup publishers
        odom_pub_ = this->create_publisher<nav_msgs::msg::Odometry>("odom", 100);
        odom_data_pub_quat_ = this->create_publisher<nav_msgs::msg::Odometry>("odom_data_quat", 100);
        odom_data_pub_euler_ = this->create_publisher<nav_msgs::msg::Odometry>("odom_data_euler", 100);

        // Setup subscribers
        left_ticks_sub_ = this->create_subscription<std_msgs::msg::Int64>(
            "left_ticks", 100,
            std::bind(&ArjunaEKFOdomPublisher::calc_left, this, std::placeholders::_1));
        right_ticks_sub_ = this->create_subscription<std_msgs::msg::Int64>(
            "right_ticks", 100,
            std::bind(&ArjunaEKFOdomPublisher::calc_right, this, std::placeholders::_1));
        initial_pose_sub_ = this->create_subscription<geometry_msgs::msg::PoseStamped>(
            "initial_2d", 1,
            std::bind(&ArjunaEKFOdomPublisher::set_initial_2d, this, std::placeholders::_1));

        // TF Broadcaster
        if (publish_tf_) {
            tf_broadcaster_ = std::make_shared<tf2_ros::TransformBroadcaster>(this);
        }

        // Timer for publishing loop
        timer_ = this->create_wall_timer(
            std::chrono::milliseconds(static_cast<int>(1000.0 / publish_rate_)),
            std::bind(&ArjunaEKFOdomPublisher::update_odom, this));

        // Parameter update callback
        parameter_callback_handle_ = this->add_on_set_parameters_callback(
            std::bind(&ArjunaEKFOdomPublisher::parameters_callback, this, std::placeholders::_1));

        RCLCPP_INFO(this->get_logger(), "=========================================");
        RCLCPP_INFO(this->get_logger(), "  Optimized Arjuna Wheel Odometry Node");
        RCLCPP_INFO(this->get_logger(), "=========================================");
        RCLCPP_INFO(this->get_logger(), "Wheel Base (Separation): %.3f m", wheel_base_);
        RCLCPP_INFO(this->get_logger(), "Wheel Radius: %.3f m", wheel_radius_);
        RCLCPP_INFO(this->get_logger(), "Ticks/Rev (Raw): %.1f | Scale: %.2f", ticks_per_revolution_, tick_scaling_);
        RCLCPP_INFO(this->get_logger(), "Calculated Ticks/Meter: %.2f", ticks_per_meter_);
        RCLCPP_INFO(this->get_logger(), "Initial Pose: x=%.3f, y=%.3f, theta=%.3f", robot_x_, robot_y_, robot_theta_);
        RCLCPP_INFO(this->get_logger(), "TF Broadcasting: %s", publish_tf_ ? "ENABLED" : "DISABLED");
        RCLCPP_INFO(this->get_logger(), "Odom Frame: %s | Base Frame: %s", odom_frame_.c_str(), base_frame_.c_str());
        RCLCPP_INFO(this->get_logger(), "Max Plausible Speed (slip threshold): %.3f m/s", max_plausible_speed_);
        RCLCPP_INFO(this->get_logger(), "=========================================");
    }

private:
    void calculate_ticks_per_meter()
    {
        double circumference = 2.0 * M_PI * wheel_radius_;
        double published_ticks_per_rev = ticks_per_revolution_ / tick_scaling_;
        ticks_per_meter_ = published_ticks_per_rev / circumference;
    }

    rcl_interfaces::msg::SetParametersResult parameters_callback(const std::vector<rclcpp::Parameter> &parameters)
    {
        rcl_interfaces::msg::SetParametersResult result;
        result.successful = true;
        result.reason = "Parameters updated successfully";
        std::lock_guard<std::mutex> lock(data_mutex_);

        bool config_changed = false;
        bool rate_changed = false;

        for (const auto &param : parameters) {
            std::string name = param.get_name();
            if (name == "wheel_radius") {
                wheel_radius_ = param.as_double();
                config_changed = true;
            } else if (name == "wheel_base") {
                wheel_base_ = param.as_double();
                config_changed = true;
            } else if (name == "ticks_per_revolution") {
                ticks_per_revolution_ = param.as_double();
                config_changed = true;
            } else if (name == "tick_scaling") {
                tick_scaling_ = param.as_double();
                config_changed = true;
            } else if (name == "publish_tf") {
                publish_tf_ = param.as_bool();
                if (publish_tf_ && !tf_broadcaster_) {
                    tf_broadcaster_ = std::make_shared<tf2_ros::TransformBroadcaster>(this);
                }
            } else if (name == "odom_frame") {
                odom_frame_ = param.as_string();
            } else if (name == "base_frame") {
                base_frame_ = param.as_string();
            } else if (name == "publish_rate") {
                double val = param.as_double();
                if (val > 0.1) {
                    publish_rate_ = val;
                    rate_changed = true;
                }
            } else if (name == "max_plausible_speed") {
                max_plausible_speed_ = param.as_double();
            }
        }

        if (config_changed) {
            calculate_ticks_per_meter();
            RCLCPP_INFO(this->get_logger(), "Updated Geometry Params: wheel_radius=%.4f, wheel_base=%.4f, ticks_per_meter=%.2f",
                        wheel_radius_, wheel_base_, ticks_per_meter_);
        }

        if (rate_changed && timer_) {
            timer_->cancel();
            timer_ = this->create_wall_timer(
                std::chrono::milliseconds(static_cast<int>(1000.0 / publish_rate_)),
                std::bind(&ArjunaEKFOdomPublisher::update_odom, this));
            RCLCPP_INFO(this->get_logger(), "Updated publish rate to %.1f Hz", publish_rate_);
        }

        return result;
    }

    void set_initial_2d(const geometry_msgs::msg::PoseStamped::SharedPtr msg)
    {
        std::lock_guard<std::mutex> lock(data_mutex_);
        robot_x_ = msg->pose.position.x;
        robot_y_ = msg->pose.position.y;
        robot_theta_ = msg->pose.orientation.z;
        RCLCPP_INFO(this->get_logger(), "Reset initial pose from /initial_2d: x=%.3f, y=%.3f, theta=%.3f",
                    robot_x_, robot_y_, robot_theta_);
    }

    void calc_left(const std_msgs::msg::Int64::SharedPtr msg)
    {
        std::lock_guard<std::mutex> lock(data_mutex_);
        if (first_left_received_) {
            first_left_received_ = false;
            lastCountL_ = msg->data;
            return;
        }

        int64_t diff = msg->data - lastCountL_;

        // Guard against anomalous encoder jumps (e.g. a glitched reading) -
        // this is a different failure mode from gradual/partial wheel slip,
        // which is instead handled in update_odom() via speed-plausibility checking.
        if (std::abs(diff) > 100000) {
            RCLCPP_WARN(this->get_logger(), "Left ticks anomalous jump detected: %ld. Resetting baseline.", diff);
            lastCountL_ = msg->data;
            return;
        }

        accumulated_left_ticks_ += diff;
        lastCountL_ = msg->data;
    }

    void calc_right(const std_msgs::msg::Int64::SharedPtr msg)
    {
        std::lock_guard<std::mutex> lock(data_mutex_);
        if (first_right_received_) {
            first_right_received_ = false;
            lastCountR_ = msg->data;
            return;
        }

        int64_t diff = msg->data - lastCountR_;

        if (std::abs(diff) > 100000) {
            RCLCPP_WARN(this->get_logger(), "Right ticks anomalous jump detected: %ld. Resetting baseline.", diff);
            lastCountR_ = msg->data;
            return;
        }

        accumulated_right_ticks_ += diff;
        lastCountR_ = msg->data;
    }

    void update_odom()
    {
        std::lock_guard<std::mutex> lock(data_mutex_);
        rclcpp::Time current_time = this->now();
        double dt = (current_time - last_time_).seconds();

        // Compute tick delta since the last publication interval
        int64_t diff_left = accumulated_left_ticks_ - timer_last_left_ticks_;
        int64_t diff_right = accumulated_right_ticks_ - timer_last_right_ticks_;

        timer_last_left_ticks_ = accumulated_left_ticks_;
        timer_last_right_ticks_ = accumulated_right_ticks_;

        // Calculate travel distance per wheel
        double d_left = static_cast<double>(diff_left) / ticks_per_meter_;
        double d_right = static_cast<double>(diff_right) / ticks_per_meter_;

        // Compute linear and angular displacements
        double distance_center = (d_right + d_left) / 2.0;
        double delta_theta = (d_right - d_left) / wheel_base_;

        // --- Wheel-slip detection ---
        // If the computed speed this cycle exceeds what the robot can
        // physically achieve, the wheel encoders are almost certainly
        // slipping (spinning faster than actual ground travel) rather than
        // reporting real motion - this is exactly what happens
        // transitioning onto/off turf sections of the arena.
        if (dt > 0.001) {
            double implied_speed = std::abs(distance_center) / dt;
            if (implied_speed > max_plausible_speed_) {
                odom_covariance_scale_ = 50.0; // sharply distrust this reading
                RCLCPP_WARN(this->get_logger(),
                    "Possible wheel slip: implied speed %.3f m/s exceeds max plausible %.3f m/s. "
                    "Inflating odometry covariance.", implied_speed, max_plausible_speed_);
            } else {
                // Decay back toward full trust over several cycles once motion
                // looks normal again, rather than snapping back instantly -
                // a slip event's effects can linger briefly after grip returns.
                odom_covariance_scale_ = std::max(1.0, odom_covariance_scale_ * 0.8);
            }
        }

        // Update 2D pose estimate using mid-point integration
        double delta_x = distance_center * std::cos(robot_theta_ + delta_theta / 2.0);
        double delta_y = distance_center * std::sin(robot_theta_ + delta_theta / 2.0);

        robot_x_ += delta_x;
        robot_y_ += delta_y;
        robot_theta_ += delta_theta;

        // Keep yaw within [-PI, PI]
        while (robot_theta_ > M_PI) robot_theta_ -= 2.0 * M_PI;
        while (robot_theta_ < -M_PI) robot_theta_ += 2.0 * M_PI;

        // Calculate velocities
        if (dt > 0.001) {
            linear_velocity_ = distance_center / dt;
            angular_velocity_ = delta_theta / dt;
        } else {
            linear_velocity_ = 0.0;
            angular_velocity_ = 0.0;
        }

        // Publish standard ROS topics
        publish_odometry_messages(current_time);

        // Broadcast transform if enabled (usually handled by robot_localization)
        if (publish_tf_ && tf_broadcaster_) {
            broadcast_tf(current_time);
        }

        last_time_ = current_time;

        // Throttled logging output
        static int log_counter = 0;
        if (++log_counter >= 90) {
            log_counter = 0;
            RCLCPP_INFO(this->get_logger(),
                        "Odom Pose: x=%.3f, y=%.3f, yaw=%.3f | Vel: lin=%.3f, ang=%.3f | CovScale=%.1f",
                        robot_x_, robot_y_, robot_theta_, linear_velocity_, angular_velocity_, odom_covariance_scale_);
        }
    }

    void publish_odometry_messages(const rclcpp::Time &stamp)
    {
        tf2::Quaternion q;
        q.setRPY(0.0, 0.0, robot_theta_);

        nav_msgs::msg::Odometry odom_msg;
        odom_msg.header.stamp = stamp;
        odom_msg.header.frame_id = odom_frame_;
        odom_msg.child_frame_id = base_frame_;

        odom_msg.pose.pose.position.x = robot_x_;
        odom_msg.pose.pose.position.y = robot_y_;
        odom_msg.pose.pose.position.z = 0.0;
        odom_msg.pose.pose.orientation.x = q.x();
        odom_msg.pose.pose.orientation.y = q.y();
        odom_msg.pose.pose.orientation.z = q.z();
        odom_msg.pose.pose.orientation.w = q.w();

        odom_msg.twist.twist.linear.x = linear_velocity_;
        odom_msg.twist.twist.linear.y = 0.0;
        odom_msg.twist.twist.linear.z = 0.0;
        odom_msg.twist.twist.angular.x = 0.0;
        odom_msg.twist.twist.angular.y = 0.0;
        odom_msg.twist.twist.angular.z = angular_velocity_;

        // Covariances scaled by odom_covariance_scale_, which is inflated
        // (see update_odom()) whenever wheel-slip is detected - this tells
        // the downstream EKF (robot_localization) to trust this reading
        // less and lean more on the IMU for that update.
        odom_msg.pose.covariance[0] = 0.01 * odom_covariance_scale_;  // x
        odom_msg.pose.covariance[7] = 0.01 * odom_covariance_scale_;  // y
        odom_msg.pose.covariance[14] = 9999.0; // z
        odom_msg.pose.covariance[21] = 9999.0; // roll
        odom_msg.pose.covariance[28] = 9999.0; // pitch
        odom_msg.pose.covariance[35] = 0.05 * odom_covariance_scale_; // yaw

        odom_msg.twist.covariance[0] = 0.01 * odom_covariance_scale_;  // vx
        odom_msg.twist.covariance[7] = 0.01 * odom_covariance_scale_;  // vy
        odom_msg.twist.covariance[14] = 9999.0; // vz
        odom_msg.twist.covariance[21] = 9999.0; // vroll
        odom_msg.twist.covariance[28] = 9999.0; // vpitch
        odom_msg.twist.covariance[35] = 0.05 * odom_covariance_scale_; // vyaw

        odom_pub_->publish(odom_msg);
        odom_data_pub_quat_->publish(odom_msg);

        // Euler topic for debugging
        nav_msgs::msg::Odometry odom_euler = odom_msg;
        odom_euler.pose.pose.orientation.z = robot_theta_;
        odom_data_pub_euler_->publish(odom_euler);
    }

    void broadcast_tf(const rclcpp::Time &stamp)
    {
        geometry_msgs::msg::TransformStamped transform;
        transform.header.stamp = stamp;
        transform.header.frame_id = odom_frame_;
        transform.child_frame_id = base_frame_;

        transform.transform.translation.x = robot_x_;
        transform.transform.translation.y = robot_y_;
        transform.transform.translation.z = 0.0;

        tf2::Quaternion q;
        q.setRPY(0.0, 0.0, robot_theta_);
        transform.transform.rotation.x = q.x();
        transform.transform.rotation.y = q.y();
        transform.transform.rotation.z = q.z();
        transform.transform.rotation.w = q.w();

        tf_broadcaster_->sendTransform(transform);
    }

    // ROS handles
    rclcpp::Publisher<nav_msgs::msg::Odometry>::SharedPtr odom_pub_;
    rclcpp::Publisher<nav_msgs::msg::Odometry>::SharedPtr odom_data_pub_quat_;
    rclcpp::Publisher<nav_msgs::msg::Odometry>::SharedPtr odom_data_pub_euler_;
    
    rclcpp::Subscription<std_msgs::msg::Int64>::SharedPtr left_ticks_sub_;
    rclcpp::Subscription<std_msgs::msg::Int64>::SharedPtr right_ticks_sub_;
    rclcpp::Subscription<geometry_msgs::msg::PoseStamped>::SharedPtr initial_pose_sub_;

    std::shared_ptr<tf2_ros::TransformBroadcaster> tf_broadcaster_;
    rclcpp::TimerBase::SharedPtr timer_;
    rclcpp::node_interfaces::OnSetParametersCallbackHandle::SharedPtr parameter_callback_handle_;

    std::mutex data_mutex_;

    // Calibration and geometry parameters
    double wheel_radius_;
    double wheel_base_;
    double ticks_per_revolution_;
    double tick_scaling_;
    double ticks_per_meter_;
    double publish_rate_;
    std::string odom_frame_;
    std::string base_frame_;
    double max_plausible_speed_; // m/s - threshold for wheel-slip detection

    // Pose and velocity state
    double robot_x_;
    double robot_y_;
    double robot_theta_;
    double linear_velocity_;
    double angular_velocity_;
    double odom_covariance_scale_; // 1.0 = normal trust, >1.0 = degraded trust (slip detected)
    
    rclcpp::Time last_time_;

    // Tick trackers
    int64_t lastCountL_;
    int64_t lastCountR_;
    int64_t accumulated_left_ticks_;
    int64_t accumulated_right_ticks_;
    int64_t timer_last_left_ticks_;
    int64_t timer_last_right_ticks_;
    
    bool first_left_received_;
    bool first_right_received_;
    bool publish_tf_;
};

int main(int argc, char **argv)
{
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<ArjunaEKFOdomPublisher>());
    rclcpp::shutdown();
    return 0;
}
