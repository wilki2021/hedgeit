'''
Created on May 14, 2013

@author: bwilkinson
'''
from pywinauto import application,findwindows
import pywinauto
import time
import traceback
import sys

def run_tssb(script, tssb_path='tssb64.exe'):
    '''
    run_tssb performs a run of TSSB for the specified script file.  If the
    function returns without exception then it can be assumed that there is 
    an AUDIT.LOG file with run results in the same directory where the script
    file is 
        
    :param string script: script file to run.  Should always be an absolute 
                          Windows-format path.
    :param string tssb_path: [Optional] path to the tssb executable.  If not 
                             specified it assumes that tssb64.exe is either in 
                             the current directory or the path of whatever 
                             shell you happen to be executing from.
                             
    :returns: No return.
    :throws:  Various exceptions possible.  Primary exception conditions are:
                - Could not locate tssb64.exe executable
                - TSSB could not locate the script file
    '''
    app = application.Application.start(tssb_path)
    time.sleep(0.5)

    # deal with the liability disclaimer first
    app.window_(title="Disclaimer of Liability").Wait('ready')
    app.window_(title="Disclaimer of Liability").IAgree.Click()
    time.sleep(0.5)
    
    # now interact with the main window
    main = app.window_(title_re="TSSB.*")
    main.Wait('ready')
    main.MenuSelect('File->Read Script')
    
    read_dlg = app.window_(title="Script file to read")
    read_dlg.Wait('ready')
    time.sleep(0.5)
    read_dlg.Edit.SetEditText(script)
    time.sleep(0.5)
    app.window_(title="Script file to read").Open.Click()
    time.sleep(0.2)
    # pywinauto is finicky here for some reason.  We need to check
    # if the window actually went away
    num = len(findwindows.find_windows(title=u'Script file to read', class_name='#32770'))
    if num == 1:
        # there is one window open which means the button press didn't 
        # take for some reason.  Let's try one more time 
        app.window_(title="Script file to read").Open.Click()
        
    # the re needs to match the script we are opening
    run_win = app.window_(title=script)
    try:
        # we have to make sure that this windows opens or else it means that
        # the script file could not be located.
        run_win.Wait('exists',timeout=2)
    except:
        # this means that the script file could not be found.  We need to
        #  1) close the error dialog
        w_handle = findwindows.find_windows(title=u'Script file to read', class_name='#32770')[0]
        window = app.window_(handle=w_handle)
        window.Close()
        time.sleep(0.5)
        #  2) close the Read Script dialog
        read_dlg.Close()
        time.sleep(0.5)
        #  3) close the main window
        app.window_(title_re="TSSB.*").MenuSelect('File->Exit')
        #  4) throw an exception so the user knows what happened 
        raise Exception('TSSB could not find script file: %s' % script)        

    # another attempt...Once the script starts it disables the menu
    while True:
        try:
            run_win.MenuSelect('File->Exit')
            break
        except pywinauto.controls.menuwrapper.MenuItemNotEnabled:
            time.sleep(1.0)
        except pywinauto.findwindows.WindowNotFoundError:
            # this is a strange case that appears to be caused when the app is 
            # too busy.  By defn our main window can't go away until we do a 
            # File->Exit so it makes no sense.  Just sleep and try again
            time.sleep(1.0)
        except:
            # this is an exception we don't expect.  Print it for debugging, 
            # but sleep and try again 
            tb = traceback.format_exc()
            print tb
            time.sleep(1.0)
    '''
    # this took much trial and error to figure out what works.  It turns out
    # that pywinauto has very little that works reliably when the application 
    # is under load and TSSB tends to do that quite often.  The one thing that
    # seems to be ok is to watch the number of child windows of our main 
    # window.  This must be > 1 at some point (there may be small risk that
    # we miss it if the script executes near instantaneously but this risk
    # seems manageable
    w_handle = findwindows.find_windows(title=script)[0]
    child_wins = len(findwindows.enum_child_windows(w_handle))
    assert( child_wins > 1)
    while child_wins > 1:
        time.sleep(1.0)
        child_wins = len(findwindows.enum_child_windows(w_handle))
    run_win.MenuSelect('File->Exit')
    ''' 
    '''
    try:
        while True:
            # use this loop to determine when TSSB is really done we know that
            # as long as TSSB is running there is an "Internal actions" window
            # although it may open/close several during a run depending on the
            # commands in the script.  We wait for one to exist and then to
            # disappear.  Note the arbitrarily long timeout on the 
            # WaitNot('exists') command - it must be long enough for the longest
            # TSSB run that we want to accommodate.  We use a short timeout on
            # the initial Wait('exists') because this is what trips us out of
            # the loop - Essentially if there is ever a 2 second period where
            # no new "Internal actions" window opens then we consider it done.
            print 'TSSB still working...',time.time()
            w_handle = findwindows.find_windows(title=script)[0]
            window = app.window_(handle=w_handle)
            window.Internalactions.Wait('exists',timeout=2)
            # window.Internalactions.WaitNot('exists',timeout=3600)
            done = False
            while not done:
                if len(findwindows.find_windows(title_re=u'Internal.*')) == 0:
                    wins = findwindows.enum_child_windows(w_handle)
                    for w in wins:
                        window = app.window_(handle=w)
                        print window
                        print window.WrapperObject().Texts()
                    print 'Internal actions not there!'
                    done = True
                else:
                    print 'Internal actions there!'
                    time.sleep(0.5)                
    except:
        print 'TSSB done...',time.time()
        # Generally speaking this is a normal condition for how we exit, thus
        # do nothing.  Some debugs in case there is a need to see which exception
        # triggered exit from our wait loop above. 
        tb = traceback.format_exc()
        print tb
        pass
    run_win.MenuSelect('File->Exit')
    ''' 
    
if __name__ == '__main__':
    run_tssb('foobar')
    scrfile = sys.argv[1]
    run_tssb(scrfile,tssb_path="C:\\Users\\bwilkinson.Calpont\\TSSB\\tssb64.exe")