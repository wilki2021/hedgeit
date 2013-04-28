'''
Created on Apr 16, 2013

@author: rtw
'''
import unittest
import hedgeit.common.observer as observer

class Test(unittest.TestCase):


    def setUp(self):
        pass


    def tearDown(self):
        pass


    def receive_it(self, parm1):
        self._value = parm1

    def receive_it2(self, parm1, parm2):
        self._value1 = parm1
        self._value2 = parm2
        
    def testBasic(self):
        e = observer.Event()

        # subscribe and try to receive the value
        e.subscribe(self.receive_it)
        self._value = None
        e.emit(99)
        self.assertEquals(self._value, 99)

        # try resubscribing
        e.subscribe(self.receive_it)

        # unsubscribe and make sure we don't get called
        e.unsubscribe(self.receive_it)
        self._value = None
        e.emit(99)
        self.assertEquals(self._value, None)

        # check that unsubscribe throws exception if not in handlers
        with self.assertRaises(ValueError):
            e.unsubscribe(self.receive_it)

        # check that emitting a list works
        e.subscribe(self.receive_it)
        e.emit([1,2,3])
        self.assertEquals(self._value, [1,2,3])

        # check that emitting a list works
        e.subscribe(self.receive_it)
        e.emit([1,2,3])
        self.assertEquals(self._value, [1,2,3])

        # try emitting the wrong number of parameters
        with self.assertRaises(TypeError):
            e.emit('hello','world')
            
        # correctly handle 2 parameters
        e.unsubscribe(self.receive_it)
        e.subscribe(self.receive_it2)
        e.emit('hello','world')
        self.assertEquals(self._value1, 'hello')
        self.assertEquals(self._value2, 'world')

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()