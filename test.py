#!/usr/bin/python3
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

def test():
	dialog = QFileDialog
	dialog.setFilter(QDir.Hidden)
	dialog.getExistingDirectory()
	
test