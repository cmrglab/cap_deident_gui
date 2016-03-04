'''
This will contain the code that will run the deidenitifcation software
on the list of provided images.

Currently, since the deidenitifcation software doesn't ouput the images into
one single directory (due to some internal grouping algo), we will circumvent
that by simply just running one image at a time and moving that image to the 
proper directory

Steps are:
for each image
1) copy it to a new temp directory
2) run the deidenitifcation on it
3) find the deidentified image
4) move it to the proper output directory
5) delete the directory the deidentified image was in
'''
import os
import sys
import shutil
import time
import tempfile
import dicom
import subprocess
import utils

class ProcessDicom():
    def __init__(self, source_dir, dest_dir, file_name_wanted, file_num_wanted,
                 userid, mem):

        self.source_dir = source_dir
        self.dest_dir = dest_dir
        self.file_name_wanted = file_name_wanted
        self.file_num_wanted = file_num_wanted
        self.userid = userid
        self.mem = mem

    def process(self):
        # Copy the the files into a working directory
        new_source_dir, new_dest_dir = self.copy_orig_images(self.file_name_wanted,
                                                             self.source_dir,
                                                             self.dest_dir)
        if not new_source_dir:
            return

        # Do the anonymization
        result = self.process_images(new_source_dir,
                            new_dest_dir,
                            self.userid,
                            self.mem)

        if result != 0:
            print("#### returning after processing, result = %s" % result)
            return 0

        # Find and move the deidentified images to the intended directory
        deident_files = self.find_files(new_dest_dir)
        if isinstance(deident_files, int):
            return 0

        if not deident_files:
            sys.stdout.write(
                "### We had an issue finding the anonymized files, we are stopping! ###\n")
            return 0
        else:
            moved = self.move_deidentified_files(deident_files, self.dest_dir, 
                    self.file_num_wanted, append = False, replace = False)

        # Clen up by removing any temporary directories that were made
        if moved:
            result = self.delete_dir(new_dest_dir)
            result2 = self.delete_dir(new_source_dir)

            if not result or not result2:
                return 0
        else:
            sys.stdout.write(
                "### We had an issue moving a file, we are stopping! ###\n")
            return 0

        return 1

    def copy_orig_images(self, files_wanted, source_dir, dest_dir):
        '''
        We need to copy the original image to a new working directory
        which will make it easier for us to find the de-identified
        file, since we will not know the name of the de-identified
        directory
        '''
        try:
            # new source dir
            new_source_dir = tempfile.mkdtemp()
            sys.stdout.write("### Working directory is: %s\n" % new_source_dir)

            # new dest dir
            new_dest_dir = os.path.join(new_source_dir, "anon")
            os.mkdir(new_dest_dir)

            # Copy the original source file to our working directory
            for f in files_wanted:
                shutil.copy(os.path.join(source_dir, f), 
                        new_source_dir)
        except Exception as msg:
            sys.stdout.write("ERROR: Could not copy file (%s) error: %s\n" % 
                (os.path.join(source_dir, f), msg))
            sys.stdout.write(
                "### We had an issue copying a file, we are stopping! ###\n")
            return 0, 0

        return new_source_dir, new_dest_dir

    def process_images(self, source_dir, dest_dir, userid, mem):
        '''
        This requires:
        1) the jar file to be located in the same directory as 
           the Python source
        2) java executable is in the PATH
        java -Xmx800m -jar CapDicomDeidentifications.jar 
        -input [original_study] -target anonymize metadata 
        -args [output_study_folder] [log_file] CAP [new_patientID]
        '''
        try:
            # These could always be passed in later, just setting them 
            # locally for now
            jar = 'CapDicomDeidentifications.jar'
            target1 = 'anonymize'
            target2 = 'metadata'
            args1 = dest_dir
            args2 = userid
            # assemble the command
            cmd2 = "java -Xmx%s -jar %s -input %s -target %s %s -args %s %s CAP %s"%\
              (mem, jar, source_dir, target1, target2, args1, args2, args2)
            print("### Running deident with: %s" % cmd2)
            result = os.system(cmd2)

        except Exception as msg:
            sys.stdout.write("ERROR: Unable to deident file, error: %s\n" % msg)
            return -1

        if result == 0:
            sys.stdout.write(
                "### Deidenitifcation completed successfully ###\n")
        else:
            sys.stdout.write(
                "### Deidenitifcation did not complete successfully ###\n")

        return result

    def find_files(self, base_dir):
        '''
        When we run the deident software we won't know the name of the 
        directory the image gets put into; however it will (should!) be 
        the only subdirectory present in the specified output directory, 
        and we just need to get its name
        '''
        # Find the directories that the de-ident software created
        dirnames = os.listdir(base_dir)

        # Now find the dicom files inside each directory
        dicom_files = []
        for directory in dirnames:
            files = os.listdir(os.path.join(base_dir, directory))

            # now see which are dicom images
            for f in files:
                try:
                    file_path = os.path.join(base_dir, directory, f)
                    dicom.read_file(os.path.join(file_path))
                    dicom_files.append(file_path)
                except Exception as msg:
                    sys.stdout.write("Warning: Found invalid DICOM file: %s\n"
                        % os.path.join(base_dir, directory, f))

            if len(dicom_files) == 0:
                sys.stdout.write("ERROR: No Dicom images found at: %s\n"
                    % os.path.join(base_dir, directory))
                return 0

        return dicom_files

    def move_deidentified_files(self, source_files, dest_file, 
                                file_num_wanted, append = False, replace = False):
        '''
        If append == True, then we will append "_#" to the file name,
        where # is the stack number of the images as computed by 
        naturally sorting the list of images.  Or that number is whatever
        is found when looking up the image number for that filename
        '''
        if append:
            filename_dict = self.sort_basenames(source_files, file_num_wanted)

        for index, f in enumerate(source_files):
            try:
                if append:
                    file_basename = utils.get_file_basename(f)
                    file_basename_no_ext = file_basename[:file_basename.rfind(".")]
                    if replace:
                        # replace exisitng appended image number with
                        # our computed index number from the original
                        # list of sorted filename
                        file_basename_no_ext = file_basename_no_ext[:file_basename.rfind("_")]

                    append_text = file_basename_no_ext + "_" +\
                                  filename_dict[file_basename] + ".dcm"
                else:
                    append_text = ''

                #print("Moving %s to %s" % (f, os.path.join(dest_file, append_text)))
                shutil.move(f, os.path.join(dest_file, append_text))
            except Exception as msg:
                sys.stdout.write("ERROR: Unable to move %s to %s. Error: %s\n" % 
                    (f, dest_file, msg))
                return 0
        return 1

    def sort_basenames(self, filename_list, file_num_wanted):
        '''
        We need to know the correct of order files after the being
        de-identified, so sort them and assign a sorted index number
        to them.
        '''
        basenames = [utils.get_file_basename(f) for f in filename_list]

        sorted_names = utils.human_sort_files(basenames)
        name_dict = {}

        for index, name in enumerate(sorted_names):
            name_dict[name] = str(file_num_wanted[index])

        return name_dict

    def delete_dir(self, dir_name):
        try:
            shutil.rmtree(dir_name)
        except   Exception as msg:
            sys.stdout.write("ERROR: Unable to delete directory: %s.  Error: %s\n" 
                % (dir_name, msg))
            return 0
        return 1
