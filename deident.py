#!/usr/bin/env python

'''
This is the user interface to the Cardiac Atlas Project's Deidentification
software.  It it currently being written with the assumption that it will
be used on Windows only. 
'''

import sys
import copy
import os
import parselist
import time
import dicom
import cProfile
import utils
from itertools import groupby
from operator import itemgetter
from processdicom import ProcessDicom
from PySide import QtCore, QtGui

class MainCanvas(QtGui.QDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)

        self.history = []
        self.numPages = 0

        self.setWindowTitle(self.tr("CAP Deidentification Interface"))
        
        self.cancel_button = QtGui.QPushButton(self.tr("Exit"))
        self.finish_button = QtGui.QPushButton(self.tr("&Deidentify"))
    
        button_layout = QtGui.QHBoxLayout()
        button_layout.addStretch(1)
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.finish_button)
    
        self.main_layout = QtGui.QVBoxLayout()
        self.main_layout.addLayout(button_layout)
        self.setLayout(self.main_layout)

        # Show the features
        self.features = Features(self)
        self.main_layout.insertWidget(0, self.features)
        self.features.show()
        self.features.setFocus()

        ######  CONNECTIONS  ######
        self.connect(self.cancel_button, QtCore.SIGNAL("clicked()"), self, QtCore.SLOT("reject()"))
        self.connect(self.finish_button, QtCore.SIGNAL("clicked()"), self.features.accept)        

class DisplayMessage(QtGui.QDialog):
    def __init__(self, parent=None, message=None):
        QtGui.QDialog.__init__(self, parent)

        self.setWindowTitle(self.tr("Display a long message"))
        
        self.exit_button = QtGui.QPushButton(self.tr("Exit"))
    
        button_layout = QtGui.QHBoxLayout()
        button_layout.addStretch(1)
        button_layout.addWidget(self.exit_button)
    
        self.main_layout = QtGui.QVBoxLayout()
        self.main_layout.addLayout(button_layout)
        self.setLayout(self.main_layout)

        # Show the message
        #QtGui.QPlainTextEdit(message)
        msg_area = QtGui.QTextBrowser()
        msg_area.setPlainText(self.tr(message))        
        self.main_layout.insertWidget(0, msg_area)
        msg_area.show()
        msg_area.setFocus()

        ######  CONNECTIONS  ######
        self.connect(self.exit_button, QtCore.SIGNAL("clicked()"), self, QtCore.SLOT("reject()"))

class Features(QtGui.QWidget):
    def __init__(self, parent):
        QtGui.QWidget.__init__(self, parent)

        # init some variables
        self.setup()

        # Show some output in the console window
        print("Running Deidentification Interface")

        self.top_label = QtGui.QLabel(self.tr("<center>"
                                             "<p>This will deidentify the Dicom images found "
                                             "in the <b>Input Directory</b>.</center>"))

        self.top_label.setWordWrap(False)
        frameStyle = QtGui.QFrame.Sunken | QtGui.QFrame.Panel   

        # Specify the input for the existing dicom images
        self.existing_directory_label = QtGui.QLabel()
        self.existing_directory_label.setFrameStyle(frameStyle)
        self.existing_directory_label.setText(self.default_dir)
        self.existing_directory_button = QtGui.QPushButton(self.tr("Set Input Directory"))

        # Specify the output for the deidentified images
        self.new_directory_label = QtGui.QLabel()
        self.new_directory_label.setFrameStyle(frameStyle)
        self.new_directory_button = QtGui.QPushButton(self.tr("Set Output Directory"))   

        # Specify how many/which images to de-ident
        self.num_images_label = QtGui.QLabel()
        self.set_which_images_label(self.get_num_images())
        self.num_images_line_edit = QtGui.QLineEdit()
        self.num_images_label.setBuddy(self.num_images_line_edit)    

        # Set the number of images to deident, default is all
        # Keep it read-only until we know how many images exist
        if self.existing_directory_label.text() == '':
            self.num_images_line_edit.setReadOnly(True)
        else:
            self.num_images_line_edit.setReadOnly(False)        

        # Specify the unique identifier to be used by the deident software 
        self.user_id_label = QtGui.QLabel()
        self.user_id_label.setText("Enter new patient identifier")
        self.user_id_line_edit = QtGui.QLineEdit()
        self.user_id_label.setBuddy(self.user_id_line_edit)         

        # Allow the user to be able to specify the memory requirements
        self.memory_label = QtGui.QLabel()
        self.memory_label.setText("Enter memory required\n(Ex: 800m is 800 MB)")
        self.memory_line_edit = QtGui.QLineEdit()
        self.memory_label.setBuddy(self.memory_line_edit)         
        # Set the default value
        self.memory_line_edit.setText('800m')

        # Connect everything to their methods
        self.connect(self.existing_directory_button, QtCore.SIGNAL("clicked()"), self.set_existing_directory)
        self.connect(self.new_directory_button, QtCore.SIGNAL("clicked()"), self.set_new_directory)    
    
        layout = QtGui.QGridLayout()
        layout.addWidget(self.top_label, 0, 0, 1, 2)
        layout.setRowMinimumHeight(1, 10)
        layout.addWidget(self.existing_directory_label, 1, 1)
        layout.addWidget(self.existing_directory_button, 1, 0)
        layout.addWidget(self.new_directory_label, 2, 1)
        layout.addWidget(self.new_directory_button, 2, 0)
        layout.addWidget(self.num_images_label, 4, 0)
        layout.addWidget(self.num_images_line_edit, 4, 1, 1, 2)
        layout.addWidget(self.user_id_label, 5, 0)
        layout.addWidget(self.user_id_line_edit, 5, 1, 1, 2)
        layout.addWidget(self.memory_label, 6, 0)
        layout.addWidget(self.memory_line_edit, 6, 1, 1, 2)

        layout.setRowStretch(1, 1)
        self.setLayout(layout)

    def setup(self):
        '''
        Initialize some variables
        '''
        self.MESSAGE_LIMIT = 2500
        self.num_existing_images = 0
        self.existing_file_names = ''

        # Very Windows specific
        # Setting the default directoy when opening our file browser
        # otherwise, it starts from where ever the source files
        # are installed
        self.default_dir = os.path.join(os.environ['SYSTEMDRIVE'] + os.path.sep,
            "Users", 
            os.environ['USERNAME'],
            "Desktop")

    def set_which_images_label(self, num_images):
        self.num_images_label.setText("Which images to deidentify (%s found)\n(Ex: 1-10 or 1,4,5, or 1-5,7,9)" % num_images)

    def set_existing_directory(self):    
        directory = QtGui.QFileDialog.getExistingDirectory(self,
                                          '',
                                          self.existing_directory_label.text(),
                                          QtGui.QFileDialog.DontResolveSymlinks | QtGui.QFileDialog.ShowDirsOnly)
        if len(directory) > 0:
            self.existing_directory_label.setText(directory)
            self.new_directory_label.setText(directory)

            # stored the filenames in a dict with some image info
            self.dicom_image_name_dict = utils.read_in_files(self, self.existing_directory_label.text())

            # do a natural sort of the file names
            self.dicom_image_name_list = utils.human_sort_files(self.dicom_image_name_dict.keys())

            # display on the GUI how many DICOM files we found
            self.set_num_images(len(self.dicom_image_name_list))

    def set_new_directory(self):    
        directory = QtGui.QFileDialog.getExistingDirectory(self,
                                          '',
                                          self.new_directory_label.text(),
                                          QtGui.QFileDialog.DontResolveSymlinks | QtGui.QFileDialog.ShowDirsOnly)
        if len(directory) > 0:
            self.new_directory_label.setText(directory)     

    def get_num_images(self):
        #self.get_existing_image_info()
        return self.num_existing_images

    def get_file_names(self):
        #self.get_existing_image_info()
        return self.existing_file_names

    def disable_user_image_selection(self):
        self.num_images_line_edit.setText('All')
        self.num_images_line_edit.setReadOnly(True)

    def set_num_images(self, total_num_images):
        ''' 
        This will simply display the number of images the user can deident 
        '''
        self.num_existing_images = total_num_images
        if total_num_images > 0:
            #self.num_images_line_edit.setText('All')
            self.num_images_line_edit.setText('1 - %s' % total_num_images)
            self.num_images_line_edit.setReadOnly(False)
        else:
            self.num_images_line_edit.setText('%s' % total_num_images)
            self.num_images_line_edit.setReadOnly(True)

        # update the GUI to show how many we found
        self.set_which_images_label(total_num_images)

    def accept(self):
        '''
        This will handle the actions once the user wants to process
        the images.
        '''
        # make sure they entered an identifier
        if not len(self.user_id_line_edit.text()) > 0:
            # display error message
            message = "Please enter a new patient identifier."
            utils.display_gui_message(self, "No indentification entered.", message)
            return

        # get the image numbers that the user entered
        image_num_wanted = \
              parselist.parse_list_reg_exp(self.num_images_line_edit.text())

        # get the filenames for the images
        image_name_wanted = []
        utils.display_message("%s files wanted..." % len(image_num_wanted))
        for num in image_num_wanted:
            try:
                # we allow users to enters image numbers starting 
                # at 1, so we need to get them back to base-zero 
                # so, subtract one
                image_name_wanted.append(self.dicom_image_name_list[num-1])
                utils.display_message("File index %s\t : Orig filename %s" %\
                                     (num, self.dicom_image_name_list[num-1]))
            except Exception as msg:
                message = "Invalid range of images wanted, image %s not in image stack" %(num)
                utils.display_message("%s" % message)
                utils.display_gui_message(self, "Invalid range of images", message)
                self.set_num_images(len(self.dicom_image_name_list))
                return


        # Set up the progress bar
        # Can't get this to work as needed
        #progress = QtGui.QProgressDialog("de-identifying files...", 
        #                                 "Abort", 
        #                                 100, 
        #                                 100, 
        #                                 self)

        #progress.setMinimumDuration(0)
        #progress.setWindowModality(QtCore.Qt.WindowModal)
        ##progress.forceShow()
        ##progress.open()
        ##progress.setVisible(True)
        ##progress.setRange(0,1)
        #progress.setValue(0)
        #progress.setRange(0,0)
        #progress.show()

        t0 = time.time()
        # now process the images
        #QtGui.qApp.processEvents() # this would get the bar to display, just not move
        self.process_image = ProcessDicom(self.existing_directory_label.text(),
                                     self.new_directory_label.text(),
                                     image_name_wanted,
                                     image_num_wanted,
                                     self.user_id_line_edit.text(),
                                     self.memory_line_edit.text())

        result = self.process_image.process()

        if not result:
            message = 'De-identification completed with issues, see console.'
            gui_message = 'De-identification completed <b>with issues</b>, see console.'
        else:
            message = 'De-identification completed successfully.'
            gui_message = 'De-identification completed <b>successfully.</b>'

        ##progress.done()
        ##progress.finished()
        ##progress.update()
        #progress.cancel()

        t1 = time.time()
        utils.display_message("Total process time: %s seconds" % (t1 - t0))

        # Let the user know we're done with this batch
        utils.display_message(message)
        utils.display_gui_message(self, "De-identification Notice.", gui_message)


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    wizard = MainCanvas()
    wizard.show()
    sys.exit(wizard.exec_())
