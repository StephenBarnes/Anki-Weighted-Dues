from aqt import mw, reviewer
from aqt.utils import showInfo
from aqt.qt import *
import re
import csv
import datetime
from anki.hooks import wrap

last_log_time = None
log_interval = datetime.timedelta(seconds=20)

def possibly_log_effective_dues(*_):
    time_now = datetime.datetime.now()
    global last_log_time
    global log_interval
    if (last_log_time is None) or (time_now > last_log_time + log_interval):
        log_dues()
        last_log_time = time_now

def log_dues():
    dues = mw.col.sched.deckDueTree()
    #print(repr(dues))

    # Find the garden 
    for item in dues:
        if item[0] != "garden":
            continue
        garden = item
        break

    garden_total_dues, garden_effective_dues = recursive_effective_dues("", garden)
    assert garden_total_dues == garden[2] + garden[3]
    print("Logging dues left, for plotting:", garden_total_dues, garden_effective_dues)
    with open("/home/j/anki-log.csv", "a") as logfile:
        csvfile = csv.writer(logfile)
        csvfile.writerow((datetime.datetime.now().timestamp(), garden_total_dues, garden_effective_dues))

def recursive_effective_dues(full_name, node):
    # Node is name, DID, green-dues, red-dues, news, tuple of children
    # This function takes in a node, returns total number of dues and effective number of dues
    name, did, greendue, reddue, news, children = node
    children_total_dues = 0
    children_effective_dues = 0
    # process total and effective dues from children
    for child in children:
        child_total, child_effective = recursive_effective_dues(full_name + "::" + child[0], child)
        children_total_dues += child_total
        children_effective_dues += child_effective

    # add total and effective dues from self
    # compute own multiplier
    multiplier_string = re.findall(r".*\{([0-9.]+)\}.*$", full_name)
    assert len(multiplier_string) in (0, 1)
    if not multiplier_string:
        own_multiplier = 1.
    else:
        try:
            own_multiplier = float(multiplier_string[0])
        except:
            print("Error: multiplier string %r, full_name %r" % (multiplier_string, full_name))
            own_multiplier = 1.
    # compute own dues
    own_dues = greendue + reddue - children_total_dues
    own_effective_dues = own_dues * own_multiplier

    return ((own_dues + children_total_dues), (own_effective_dues + children_effective_dues)) 

# create a new menu item to log effective dues
action = QAction("Log Effective Dues", mw)
action.triggered.connect(log_dues)
mw.form.menuTools.addAction(action)

# make it run automatically on deckbrowser.show
#from aqt.deckbrowser import DeckBrowser
#DeckBrowser.show = wrap(DeckBrowser.show, log_dues)
# to enable this, make log_dues take arguments: (*_)

# make it run automatically after card-answering
reviewer.Reviewer._answerCard = wrap(reviewer.Reviewer._answerCard, possibly_log_effective_dues, "before")

