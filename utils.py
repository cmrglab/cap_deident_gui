import sys
import os
import dicom
import operator
import re
import pickle
import time
from PySide import QtCore, QtGui
from natsort import natsorted

def display_gui_message(parent, window_title, message):    
    # Only print a portion of the message
    if len(message) > parent.MESSAGE_LIMIT:
        message = message[:parent.MESSAGE_LIMIT]
        message += "\n...listing shortened for ease of display."
    QtGui.QMessageBox.information(parent, parent.tr(window_title), message)

def display_message(message):
    '''
    Just writes out a message to the screen using a common format.
    '''
    sys.stdout.write("### %s ###\n" % message)

def create_logfile():
    basename = 'deident'
    unique_string = str(time.time())

    logfile = open((basename + "+" + unique_string + ".log"), "w")

    return logfile

def is_dicom(filename):
    '''
    This will return True if the supplied file is a Dicom image,
    and will return False otherwise.
    We don't want to have to open each file twice, to get
    any other image data we need now

    Our simple test is to try to read it in with PyDicom
    '''
    try:
        dfile = dicom.read_file(filename)
        return True
    except Exception:
        self.display_message('%s is not a valid Dicom file' % filename)
        return False

def is_dicom_with_file_info(filename):
    '''
    This will return True if the supplied file is a Dicom image,
    and will return False otherwise.
    We don't want to have to open each file twice, to get
    any other image data we need now

    Our simple test is to try to read it in with PyDicom
    '''
    try:
        dfile = dicom.read_file(filename)
        file_basename = filename[filename.rfind("\\")+1:]
        image_num = dfile.InstanceNumber

        print("File: %s ImageNum: %s AcquisitionNum: %s SeriesNum: %s" %(file_basename,
            image_num, dfile.AcquisitionNumber, dfile.SeriesNumber))
        return True, image_num, dfile.AcquisitionNumber, dfile.SeriesNumber
    except Exception as msg:
        display_message('%s is not a valid Dicom file' % filename)
        return False, None, None, None

def get_file_basename(filename):
    return filename[filename.rfind(os.path.sep)+1:]

def human_sort_files(filename_list):
    '''
    We need to make sure that the filenames are sorted numerically and that
    in a given series, all the image numbers are sorted in ascending order
    '''
    return natsorted(filename_list)
    '''
    values = natsorted(filename_dict.keys())

    new_list = []
    for key in filename_dict.keys():
        new_list.append(filename_dict[key].insert(0,key))


    # now we want to make sure that for a given series, all of the 
    # image numbers are in ascending order
    # First sort by filename
    list1 = natsorted(filename_dict.values(), key=operator.itemgetter(0))
    pprint.pprint(list1)
    # then by series
    list2 = sorted(list1, key=operator.itemgetter(3))
    pprint.pprint(list2)
    # last by image number
    list3 = sorted(list2, key=operator.itemgetter(1))
    pprint.pprint(list3)

    return list3
    '''

def read_in_files(parent, directory_name, gui = True):
    ''' 
    This will find the number of dicom images in the supplied directory_name
    '''
    dicom_image_name_dict = {}
    file_names = os.listdir(directory_name)

    # set up a progress bar
    if gui:
        progress = QtGui.QProgressDialog("Scanning files...", 
                                         "Abort Scanning", 
                                         0, 
                                         len(file_names), 
                                         parent)
        progress.setMinimumDuration(1)
        progress.setWindowModality(QtCore.Qt.WindowModal)

    file_count = 0
    display_message("Scanning files")
    for count, my_file in enumerate(file_names):
        file_basename = get_file_basename(my_file)

        if gui:
            if progress.wasCanceled():
                break

        # Determine if this is a Dicom image or not
        is_dicom, image_num, image_acq, image_series = \
            is_dicom_with_file_info(os.path.join(directory_name, my_file))

        if is_dicom:
            file_count += 1

            # store this file's info
            dicom_image_name_dict[file_basename] = [image_num, image_acq, image_series]

        if gui: 
            progress.setValue(count)

    display_message("Found %s total files of which %s are Dicom images" 
        % (len(file_names), file_count))

    if gui:
        progress.setValue(len(file_names))

    create_answer = False
    if create_answer:
        pickle.dump(dicom_image_name_dict, open("ans.pickle", "wb"), -1)

    return dicom_image_name_dict
