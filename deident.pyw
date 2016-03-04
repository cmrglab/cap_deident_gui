#!/usr/bin/env python

'''This is the user interface to the Cardiac Atlas Project's Deidentification
    software.  It it currently being written with the assumption that it will
    be used on Windows only. '''

import sys
import os
import parselist
import time
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

class Features(QtGui.QWidget):
    def __init__(self, parent):
        QtGui.QWidget.__init__(self, parent)

        self.dcm_extension = 'dcm'
        self.read_images = False

        # Show some output in the console window
        print("Running Deidentification Interface")

        self.top_label = QtGui.QLabel(self.tr("<center>"
                                             "<p>This will deidentify the Dicom images found "
                                             "in the <b>Input Directory</b>.</center>"))

        self.top_label.setWordWrap(False)
        frameStyle = QtGui.QFrame.Sunken | QtGui.QFrame.Panel   

        # Specify the input for the existing dicom images
        self.exisitng_directory_label = QtGui.QLabel()
        self.exisitng_directory_label.setFrameStyle(frameStyle)
        self.exisitng_directory_button = QtGui.QPushButton(self.tr("Set Input Directory"))

        # Specify the output for the deidentified images
        self.new_directory_label = QtGui.QLabel()
        self.new_directory_label.setFrameStyle(frameStyle)
        self.new_directory_button = QtGui.QPushButton(self.tr("Set Output Directory\n(must be empty)"))   

        # Specify how many/which images to de-ident
        self.num_images_label = QtGui.QLabel()
        self.set_which_images_label(self.get_num_images())
        self.num_images_line_edit = QtGui.QLineEdit()
        self.num_images_label.setBuddy(self.num_images_line_edit)    

        # Set the number of images to deident, default is all
        # Keep it read-only until we know how many images exist
        if self.exisitng_directory_label.text() == '':
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
        self.connect(self.exisitng_directory_button, QtCore.SIGNAL("clicked()"), self.set_existing_directory)
        self.connect(self.new_directory_button, QtCore.SIGNAL("clicked()"), self.set_new_directory)    
    
        layout = QtGui.QGridLayout()
        layout.addWidget(self.top_label, 0, 0, 1, 2)
        layout.setRowMinimumHeight(1, 10)
        layout.addWidget(self.exisitng_directory_label, 1, 1)
        layout.addWidget(self.exisitng_directory_button, 1, 0)
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

    def set_which_images_label(self, num_images):
        self.num_images_label.setText("Which images to deidentify (%s found)\n(Ex: 1-10 or 1,4,5, or 1-5,7,9)" % num_images)

    def set_existing_directory(self):    
        directory = QtGui.QFileDialog.getExistingDirectory(self,
                                          self.tr("Input Directory"),
                                          self.exisitng_directory_label.text(),
                                          QtGui.QFileDialog.DontResolveSymlinks | QtGui.QFileDialog.ShowDirsOnly)
        if directory is not '':
            self.exisitng_directory_label.setText(directory)
            self.set_num_images(self.get_num_images())


    def set_new_directory(self):    
        directory = QtGui.QFileDialog.getExistingDirectory(self,
                                          self.tr("Output Directory"),
                                          self.new_directory_label.text(),
                                          QtGui.QFileDialog.DontResolveSymlinks | QtGui.QFileDialog.ShowDirsOnly)
        if directory is not '':
            self.new_directory_label.setText(directory)     

    def get_num_images(self):
        self.get_existing_image_info()
        return self.num_existing_images

    def get_file_names(self):
        self.get_existing_image_info()
        return self.existing_file_names

    def get_existing_image_info(self):
        ''' This will find the number of dicom images in 'exisitng_directory_label'
            This assumes the extension is some variant of dcm '''

        self.num_existing_images = 0
        self.existing_file_names = ''

        if self.exisitng_directory_label.text() == '':
            return 0

        file_names = os.listdir(self.exisitng_directory_label.text())
        file_count = 0
        for my_file in file_names:
            if my_file[-3:].lower() == self.dcm_extension:
                file_count += 1

        self.write_notice("Found %s Dicom files" % len(file_names))

        self.set_num_images(self.num_existing_images)
        self.num_existing_images = file_count
        self.existing_file_names = file_names

    def set_num_images(self, total_num_images):
        ''' This will simply display the number of images the user can deident '''
        if total_num_images > 0:
            self.num_images_line_edit.setText('1 - %s' % total_num_images)
            self.num_images_line_edit.setReadOnly(False)
        else:
            self.num_images_line_edit.setText('%s' % total_num_images)
            self.num_images_line_edit.setReadOnly(True)

        # update the GUI to show how many we found
        self.set_which_images_label(total_num_images)

    def accept(self):
        # verify the desired images are valid
        images_wanted = \
                  parselist.parse_list_reg_exp(self.num_images_line_edit.text())

        self.write_notice("images wanted: %s" % images_wanted)

        # just a simple check for min/max within the acceptable bounds
        if min(images_wanted) < 1 or \
           max(images_wanted) > self.num_existing_images:
            sys.stderr.write(
                "ERROR: Invalid range of images wanted, please try again\n")
            self.set_num_images(self.get_num_images())
            return

        # now process each image
        for image in images_wanted:
            # Remember to account for the numbering to be off by one for the list
            print("Working on image[%s]: %s" % (image, self.existing_file_names[image-1]))

            process_image = ProcessDicom(self.exisitng_directory_label.text(),
                                         self.new_directory_label.text(),
                                         self.existing_file_names[image-1],
                                         self.user_id_line_edit.text(),
                                         self.memory_line_edit.text())

            self.write_notice("Processed image [%s] of [%s]" % (image, len(images_wanted)))

        # Let the user know we're done with this batch
        message = 'All images have been deidentified.'
        self.write_notice(message)
        self.informationMessage(message)

    def informationMessage(self, message):    
        QtGui.QMessageBox.information(self, self.tr("Deidentification complete!"), message)
        #self.informationLabel.setText(self.tr("Closed with OK or Esc"))

    def write_notice(self, message):
        sys.stdout.write("### %s ###\n" % message)

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    wizard = MainCanvas()
    wizard.show()
    sys.exit(wizard.exec_())
