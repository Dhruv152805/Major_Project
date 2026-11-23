import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/dhruv/Arjuna_ws_team3/install/arjuna_baseline'
