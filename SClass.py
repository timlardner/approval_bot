import pickle
import datetime
import praw

class ManageApproved:
    def __init__(self):
        # Authenticate
        reddit = praw.Reddit('sbot',user_agent="Testing API functons, /u/timlardner")
        self.subreddit = reddit.subreddit('steroids')
        # Get a list of approved submitters
        self.contrib_list = []
        for user in self.subreddit.contributor(limit=None):
            self.contrib_list.append(str(user))
        print('There are',len(self.contrib_list),'users already approved')
        self.waitlist = WaitList()
    def getNewPosts(self):
        count = 0
        count2 = 0
        for comment in self.subreddit.comments(limit=None):
            count2 = count2+1
            commenttime=datetime.datetime.utcfromtimestamp(comment.created_utc)
            delta = datetime.datetime.utcnow() - commenttime
            if delta >  datetime.timedelta(hours=13):
                break
            if str(comment.author) in self.contrib_list:
                continue
            new_comment = WaitItem(comment.author,commenttime,90)
            count = count + self.waitlist.add(new_comment)
        print(count,'users added to the waiting list from',count2,'comments processed in total')
        self.waitlist.save()
    def processWaitingList(self):
        self.waitlist.checkRemoves()
        self.waitlist.doRemoves(self.subreddit)
        self.waitlist.save()
    
class WaitList:
    def __init__(self):
        # Open the file and populate waitlist 
        self.filename = 'Waitlist.bin'
        try:
            self.waitlist = pickle.load( open( self.filename, "rb" ) )
        except:
            self.waitlist = []
        print('There are',len(self.waitlist),'users waiting to be approved')
    def add(self,item):
        for existing in self.waitlist:
            if existing.author == item.author:
                if item.approve_date < existing.approve_date:
                    existing.approve_date = item.approve_date
                return int(0)
        self.waitlist.append(item)
        return int(1)
    def checkRemoves(self):
        count = 0 
        first_date = datetime.datetime.utcnow() + datetime.timedelta(days=90)
        for item in self.waitlist:
            if item.approve_date < first_date:
                first_date = item.approve_date
            if item.approve_date < datetime.datetime.utcnow():
                item.remove = True
                count = count+1
        print(count,'users to be approved')
        if count == 0:
            print('Next approval to take place on',first_date)
    def doRemoves(self,sub):
        newlist = []
        for item in self.waitlist:
            if item.remove is True:
                sub.contributor.add(item.author)
                continue
            newlist.append(item)
        self.waitlist = newlist
    def save(self):
        pickle.dump(self.waitlist,open(self.filename,'wb'))
   
class WaitItem:
    def __init__(self,user,date,waitdays):
        self.author = user
        self.date = date
        self.approve_date = self.date + datetime.timedelta(days=waitdays)
        self.remove = False        
        
if __name__ == "__main__":
    print('Running code')
    approver = ManageApproved()
    approver.getNewPosts()
    approver.processWaitingList()
    print('Done')

