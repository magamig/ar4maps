# *****************************************************************************
# * Author: Miguel Magalhaes
# * Email: miguel@magalhaes.pro
# *****************************************************************************
# * Main
# *****************************************************************************

import sys
import yaml
from PyQt5.QtWidgets import QApplication

from interface import Interface

if __name__ == "__main__": 
    app = QApplication(sys.argv)
    with open(sys.argv[1] + 'config.yml') as f:
        config = yaml.safe_load(f)
        win = Interface(sys.argv[1], config)
        win.show()
    sys.exit(app.exec_())
