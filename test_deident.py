'''
This will do some simple testing on the CAP De-identification GUI
'''
import os
import utils
import processdicom
import pickle
import parselist

class test_deident():
    def __init__(self):
        pass

    def test_read_no_dicom_files(self):
        directory = os.path.join(os.getcwd(), "test_data", "data1")
        test_dict = utils.read_in_files(self, directory, gui = False)

        answer = self.get_answer("no_dicom_files_ans.pickle")
        assert test_dict == answer

    def test_read_some_dicom_files(self):
        directory = os.path.join(os.getcwd(), "test_data", "data2")
        test_dict = utils.read_in_files(self, directory, gui = False)

        answer = self.get_answer("some_dicom_files_ans.pickle")
        assert test_dict == answer

    def test_read_lots_dicom_files(self):
        directory = os.path.join(os.getcwd(), "test_data", "data3")
        test_dict = utils.read_in_files(self, directory, gui = False)

        answer = self.get_answer("lots_dicom_files_ans.pickle")
        assert test_dict == answer

    def test_parse_num(self):
        nums = ['1-10', 
                '1,2,3,4,5',
                '2,4,6,8',
                '1-5,7,10',
                '1-5,7,8,9-12']

        ans = [[1,2,3,4,5,6,7,8,9,10],
               [1,2,3,4,5],
               [2,4,6,8],
               [1,2,3,4,5,7,10],
               [1,2,3,4,5,7,8,9,10,11,12]]

        for index in xrange(len(nums)):
            result = parselist.parse_list_reg_exp(nums[index])
            assert result == ans[index], ("%s not equal to %s\n" % (result, ans[index]))

    def get_answer(self, filename):
        ans = os.path.join(os.getcwd(), "test_data", "answers", filename)
        return pickle.load(open(ans, "rb"))

if __name__ == '__main__':
    tests = test_deident()
