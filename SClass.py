import pickle
import datetime
import praw

class ManageApproved:
    
    def __init__(self):
        # Authenticate and pick a subreddit
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
        # Get all comments from subreddit
        for comment in self.subreddit.comments(limit=None):
            count2 = count2+1
            commenttime=datetime.datetime.utcfromtimestamp(comment.created_utc)
            delta = datetime.datetime.utcnow() - commenttime
            # We run every 12 hours so try to pick up all comments made since the last run
            # The API will return a maximum of 1000 comments so on more active subreddits, it'll need to be run more often
            if delta >  datetime.timedelta(hours=13):
                break
            
            # If the author is already an approved submitter, don't do anything
            if str(comment.author) in self.contrib_list:
                continue
            
            # Otherwise create a new WaitItem object and increment the counter    
            new_comment = WaitItem(comment.author,commenttime,90)
            count = count + self.waitlist.add(new_comment)
        print(count,'users added to the waiting list from',count2,'comments processed in total')
        # Make sure we're always writing the array of WaitItems to disk
        self.waitlist.save()
        
    def processWaitingList(self):
        # Once we've got all the recent posts, see if anyone needs to be approved
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
            # Check our waiting list to see if the author's already in it
            # If this is an older comment, update the approval date with the new one but don't add a second entry to the waiting list
            if existing.author == item.author:
                if item.approve_date < existing.approve_date:
                    existing.approve_date = item.approve_date
                return int(0)
        self.waitlist.append(item)
        return int(1)
    def checkRemoves(self):
        count = 0 
        # Just to keep track of the next person due to be approved
        first_date = datetime.datetime.utcnow() + datetime.timedelta(days=90)
        for item in self.waitlist:
            if item.approve_date < first_date:
                first_date = item.approve_date
            if item.approve_date < datetime.datetime.utcnow():
                # If we're past the approval date, set the remove flag to True and we'll approve it on the next pass
                item.remove = True
                count = count+1
        print(count,'users to be approved')
        if count == 0:
            print('Next approval to take place on',first_date)
    def doRemoves(self,sub):
        newlist = []
        for item in self.waitlist:
            if item.remove is True:
                # If the approve flag is set, add the user as a contributor
                print('Approving',item.author)
                sub.contributor.add(item.author)
                continue
            # If the approve flag is not set, add the user to a new array
            # This is easier than removing elements from the existing list
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

