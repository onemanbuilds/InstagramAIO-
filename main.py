from colorama import init,Fore
from threading import Thread, Lock
from multiprocessing.dummy import Pool as ThreadPool
from datetime import datetime
from bs4 import BeautifulSoup
from instagram_private_api import ClientCompatPatch,Client, ClientError, ClientLoginError,ClientCookieExpiredError, ClientLoginRequiredError
import sys
import os
import json
import codecs
import time
import requests
import string
import random

class Main:
    def clear(self):
        if os.name == 'posix':
            os.system('clear')
        elif os.name in ('ce', 'nt', 'dos'):
            os.system('cls')
        else:
            print("\n") * 120

    def SetTitle(self,title_name:str):
        os.system("title {0}".format(title_name))

    def ReadConfig(self):
        with open('configs.json','r') as f:
            config = json.load(f)
        return config

    def to_json(self,python_object):
        if isinstance(python_object, bytes):
            return {'__class__': 'bytes',
                    '__value__': codecs.encode(python_object, 'base64').decode()}
        raise TypeError(repr(python_object) + ' is not JSON serializable')

    def from_json(self,json_object):
        if '__class__' in json_object and json_object['__class__'] == 'bytes':
            return codecs.decode(json_object['__value__'].encode(), 'base64')
        return json_object

    def onlogin_callback(self,api, new_settings_file):
        cache_settings = api.settings
        with open(new_settings_file, 'w') as outfile:
            json.dump(cache_settings, outfile, default=self.to_json)
            self.PrintText('SAVED','{0!s}'.format(new_settings_file),Fore.MAGENTA,Fore.MAGENTA)

    def Login(self,username,password):
        device_id = None
        api = None

        try:
            settings_file = 'info.json'
            if not os.path.isfile(settings_file):
                # settings file does not exist
                self.PrintText('UNABLE TO FIND FILE','{0!s}'.format(settings_file),Fore.MAGENTA,Fore.MAGENTA)

                # login new
                api = Client(username, password,on_login=lambda x: self.onlogin_callback(x, settings_file))
            else:
                with open(settings_file) as file_data:
                    cached_settings = json.load(file_data, object_hook=self.from_json)
                
                self.PrintText('REUSING SETTINGS','{0!s}'.format(settings_file),Fore.MAGENTA,Fore.MAGENTA)

                device_id = cached_settings.get('device_id')
                # reuse auth settings
                api = Client(username, password,settings=cached_settings)
        except (ClientCookieExpiredError, ClientLoginRequiredError) as e:
            self.PrintText('ClientCookieExpiredError/ClientLoginRequiredError','{0!s}'.format(e),Fore.RED,Fore.RED)

            # Login expired
            # Do relogin but use default ua, keys and such
            api = Client(username, password,device_id=device_id,on_login=lambda x: self.onlogin_callback(x, settings_file))
        except ClientLoginError as e:
            self.PrintText('ClientLoginError','{0!s}'.format(e),Fore.RED,Fore.RED)
        except ClientError as e:
            self.PrintText('ClientError {0!s}','(Code: {1:d}, Response: {2!s})'.format(e.msg, e.code, e.error_response),Fore.RED,Fore.RED)
        except Exception as e:
            self.PrintText('Unexpected Exception','{0!s}'.format(e),Fore.RED,Fore.RED)

        # Show when login expires
        #cookie_expiry = api.cookie_jar.auth_expires
        #print('Cookie Expiry: {0!s}'.format(datetime.datetime.fromtimestamp(cookie_expiry).strftime('%Y-%m-%dT%H:%M:%SZ')))
        return api

    def __init__(self):
        #removed reportbot
        #removed accept all followers
        #removed decline all followers
        
        self.options = ['Follow Bot','Just Follow','Just Unfollow','Like Bot','Just Like','Just Unlike','Comment Bot','Username Checker','Stories Viewer','Follow by Hashtag','Unfollow by Hashtag','Download Videos / Images','Grab Avatars','Account Checker','Username Scraper']
        
        config = self.ReadConfig()
        self.username = config['username']
        self.password = config['password']
        self.followbot_option = config['followbot_option']
        self.followbot_timeout = config['followbot_timeout']
        self.likebot_option = config['likebot_option']
        self.likebot_timeout = config['likebot_timeout']
        self.comment_timeout = config['comment_timeout']
        self.download_videos_or_images_timeout = config['download_videos_or_images_timeout']
        self.download_videos_or_images_option = config['download_videos_or_images_option'] #az optiont checkelni ha 1 akk media_urls.txtből downloadolgasson ha más akk pedig 1 urlből
        self.download_avatars_timeout = config['download_avatars_timeout']
        self.download_avatars_option = config['download_avatars_option'] #az optiont checkelni ha 1 akk usernames.txtből downloadolgasson ha más akk pedig 1 urlből
        self.username_checker_use_proxies = config['username_checker_use_proxies']
        self.username_checker_timeout = config['username_checker_timeout']
        self.account_checker_use_proxies = config['account_checker_use_proxies']
        self.account_checker_timeout = config['account_checker_timeout']
        self.BOLD = '\033[1m'

        init(autoreset=True,convert=True)
        self.clear()
        self.api = self.Login(self.username,self.password)
        time.sleep(2)
        try:
            self.cookie_expire_date = datetime.fromtimestamp(self.api.cookie_jar.auth_expires).strftime('%Y-%m-%d %H:%M:%S')
            self.SetTitle('One Man Builds Instagram AIO++ Tool [WELCOME: {0}] [LOGIN EXPIRES: {1}]'.format(self.api.authenticated_user_name,self.cookie_expire_date))
        except:
            pass
        

    def ReadFile(self,filename,method):
        with open(filename,method) as f:
            content = [line.strip('\n') for line in f]
            return content

    def PrintText(self,info_name,text,info_color:Fore,text_color:Fore):
        lock = Lock()
        lock.acquire()
        sys.stdout.flush()
        text = text.encode('ascii','replace').decode()
        sys.stdout.write(self.BOLD+'{0}[{1}{2}{3}] '.format(info_color,Fore.RESET,info_name,info_color)+text_color+f'{text}\n')
        lock.release()

    def PrintInput(self,info_name,text,bracket_color:Fore,info_color:Fore,text_color:Fore):
        print('')
        option = input(self.BOLD+bracket_color+'['+info_color+info_name+bracket_color+'] '+text_color+text+info_color+': ')
        return option

    def Menu(self):
        self.clear()
        item_count = 0
        for item in self.options:
            item_count = item_count+1
            self.PrintText(str(item_count),item,Fore.MAGENTA,Fore.MAGENTA)
        
        option = self.PrintInput('OPTION','Choose something',Fore.MAGENTA,Fore.WHITE,Fore.MAGENTA)
        print('')

        if int(option) == 1:
            usernames = self.ReadFile('Data/[Follow Bot]/usernames.txt','r')
            pool = ThreadPool()
            results = pool.map(self.FollowBot,usernames)
            pool.close()
            pool.join()
            time.sleep(2)
            self.Menu()
        elif int(option) == 2:
            usernames = self.ReadFile('Data/[Just Follow]/usernames.txt','r')
            pool = ThreadPool()
            results = pool.map(self.Follow,usernames)
            pool.close()
            pool.join()
            time.sleep(2)
            self.Menu()
        elif int(option) == 3:
            usernames = self.ReadFile('Data/[Just Unfollow]/usernames.txt','r')
            pool = ThreadPool()
            results = pool.map(self.UnFollow,usernames)
            pool.close()
            pool.join()
            time.sleep(2)
            self.Menu()
        elif int(option) == 4:
            media_urls = self.ReadFile('Data/[Like Bot]/media_urls.txt','r')
            pool = ThreadPool()
            results = pool.map(self.LikeBot,media_urls)
            pool.close()
            pool.join()
            time.sleep(2)
            self.Menu()
        elif int(option) == 5:
            media_urls = self.ReadFile('Data/[Just Like]/media_urls.txt','r')
            pool = ThreadPool()
            results = pool.map(self.Like,media_urls)
            pool.close()
            pool.join()
            time.sleep(2)
            self.Menu()
        elif int(option) == 6:
            media_urls = self.ReadFile('Data/[Just Unlike]/media_urls.txt','r')
            pool = ThreadPool()
            results = pool.map(self.UnLike,media_urls)
            pool.close()
            pool.join()
            time.sleep(2)
            self.Menu()
        elif int(option) == 7:
            media_urls = self.ReadFile('Data/[Comment Bot]/media_urls.txt','r')
            pool = ThreadPool()
            results = pool.map(self.Comment,media_urls)
            pool.close()
            pool.join()
            time.sleep(2)
            self.Menu()
        elif int(option) == 8:
            usernames = self.ReadFile('Data/[Username Checker]/usernames.txt','r')
            pool = ThreadPool()
            results = pool.map(self.UsernameChecker,usernames)
            pool.close()
            pool.join()
            time.sleep(2)
            self.Menu()
        elif int(option) == 9:
            usernames = self.ReadFile('Data/[Stories Viewer]/usernames.txt','r')
            pool = ThreadPool()
            results = pool.map(self.StoryViewer,usernames)
            pool.close()
            pool.join()
            time.sleep(2)
            self.Menu()
        elif int(option) == 10:
            threading = Thread(target=self.FollowByHashtag).start()
            time.sleep(5)
            self.Menu()
        elif int(option) == 11:
            threading = Thread(target=self.UnFollowByHashtag).start()
            time.sleep(5)
            self.Menu()
        elif int(option) == 12:
            if self.download_videos_or_images_option == 1:
                media_urls = self.ReadFile('Data/[Downloads]/media_urls.txt','r')
                pool = ThreadPool()
                results = pool.map(self.DownloadVideosOrImages,media_urls)
                pool.close()
                pool.join()
            else:
                threading = Thread(target=self.DownloadVideoOrImage).start()
            time.sleep(2)
            self.Menu()
        elif int(option) == 13:
            if self.download_avatars_option == 1:
                usernames = self.ReadFile('Data/[Grab Avatars]/usernames.txt','r')
                pool = ThreadPool()
                results = pool.map(self.DownloadAvatars,usernames)
                pool.close()
                pool.join()
            else:
                threading = Thread(target=self.DownloadAvatar).start()

            time.sleep(2)
            self.Menu()
        elif int(option) == 14:
            combos = self.ReadFile('Data/[Account Checker]/combos.txt','r')
            pool = ThreadPool()
            results = pool.map(self.AccountChecker,combos)
            pool.close()
            pool.join()
            time.sleep(2)
            self.Menu()
        elif int(option) == 15:
            threading = Thread(target=self.UsernameScrape).start()
            time.sleep(5)
            self.Menu()
        else:
            threading = Thread(target=self.DownloadVideoOrImage).start()
            time.sleep(2)
            self.Menu()

    def GetUserId(self,username):
        response = requests.get('https://www.instagram.com/{0}/?__a=1'.format(username)).text
        json_data = json.loads(response)
        if 'graphql' in json_data:
            return json_data['graphql']['user']['id']
        else:
            return 'CAN NOT GET {0} ID'.format(username)
        

    def GetMediaId(self,media_url):
        response = requests.get('https://api.instagram.com/oembed/?callback=&url={0}'.format(media_url)).text
        json_data = json.loads(response)
        if 'media_id' in json_data:
            return json_data['media_id']
        else:
            return 'CAN NOT GET {0} ID'.format(media_url)
        

    def GetMediaThumbnailFullUrl(self,media_url):
        response = requests.get('https://api.instagram.com/oembed/?callback=&url={0}'.format(media_url)).text
        json_data = json.loads(response)
        if 'thumbnail_url' in json_data:
            return json_data['thumbnail_url']
        else:
            return 'CAN NOT GET {0} ID'.format(media_url)
        
    def Follow(self,username):
        try:
            userid = self.GetUserId(username)
            result = self.api.friendships_create(userid)
            #timeout = self.PrintInput('TIMEOUT','Enter the timeout after unfollows',Fore.MAGENTA,Fore.WHITE,Fore.MAGENTA)
            if 'friendship_status' in result:
                if result['friendship_status']['following'] == True:
                    self.PrintText('FOLLOWED',username,Fore.GREEN,Fore.GREEN)
                    with open('Data/[Just Follow]/results.txt','a') as f:
                        f.write('FOLLOWED {0}\n'.format(username))
                else:
                    self.PrintText('ALREADY FOLLOWING',username,Fore.RED,Fore.RED)
                    with open('Data/[Just Follow]/results.txt','a') as f:
                        f.write('ALREADY FOLLOWING {0}\n'.format(username))
            else:
                self.PrintText('ERROR','SOMETHING WENT WRONG',Fore.RED,Fore.RED)
        except:
            pass

    def UnFollow(self,username):
        try:
            userid = self.GetUserId(username)
            result = self.api.friendships_destroy(userid)
            #timeout = self.PrintInput('TIMEOUT','Enter the timeout after unfollows',Fore.MAGENTA,Fore.WHITE,Fore.MAGENTA)
            if 'friendship_status' in result:
                if result['friendship_status']['following'] == False:
                    self.PrintText('UNFOLLOWED',username,Fore.GREEN,Fore.GREEN)
                    with open('Data/[Just Unfollow]/results.txt','a') as f:
                            f.write('UNFOLLOWED {0}\n'.format(username))
                else:
                    self.PrintText('YOU ARE ALREADY NOT FOLLOWING',username,Fore.RED,Fore.RED)
                    with open('Data/[Just Unfollow]/results.txt','a') as f:
                            f.write('YOU ARE ALREADY NOT FOLLOWING {0}\n'.format(username))
            else:
                self.PrintText('ERROR','SOMETHING WENT WRONG',Fore.RED,Fore.RED)
        except:
            pass
        
    def FollowById(self,userid):
        try:
            userid = self.GetUserId(username)
            result = self.api.friendships_create(userid)
            followed = 0
            #timeout = self.PrintInput('TIMEOUT','Enter the timeout after unfollows',Fore.MAGENTA,Fore.WHITE,Fore.MAGENTA)
            if 'friendship_status' in result:
                if result['friendship_status']['following'] == True:
                    self.PrintText('FOLLOWED',userid,Fore.GREEN,Fore.GREEN)
                    with open('Data/[Just Follow]/follow_by_id_results.txt','a') as f:
                        f.write('FOLLOWED {0}\n'.format(userid))
                    followed = 1
                else:
                    self.PrintText('ALREADY FOLLOWING',userid,Fore.RED,Fore.RED)
                    with open('Data/[Just Follow]/follow_by_id_results.txt','a') as f:
                        f.write('ALREADY FOLLOWING {0}\n'.format(userid))
                    followed = 2
            else:
                self.PrintText('ERROR','SOMETHING WENT WRONG',Fore.RED,Fore.RED)

            if self.follow_timeout > 0:
                time.sleep(self.follow_timeout)

            return followed
        except:
            pass

    def UnfollowById(self,userid):
        try:
            result = self.api.friendships_destroy(userid)
            unfollowed = 0
            #timeout = self.PrintInput('TIMEOUT','Enter the timeout after unfollows',Fore.MAGENTA,Fore.WHITE,Fore.MAGENTA)
            if 'friendship_status' in result:
                if result['friendship_status']['following'] == False:
                    self.PrintText('UNFOLLOWED',userid,Fore.GREEN,Fore.GREEN)
                    with open('Data/[Just Unfollow]/unfollow_by_id_results.txt','a') as f:
                        f.write('UNFOLLOWED {0}\n'.format(userid))
                    unfollowed = 1
                else:
                    self.PrintText('YOU ARE ALREADY NOT FOLLOWING',userid,Fore.RED,Fore.RED)
                    with open('Data/[Just Unfollow]/unfollow_by_id_results.txt','a') as f:
                        f.write('YOU ARE ALREADY NOT FOLLOWING {0}\n'.format(userid))
                    unfollowed = 2
            else:
                self.PrintText('ERROR','SOMETHING WENT WRONG',Fore.RED,Fore.RED)

            if self.unfollow_timeout > 0:
                time.sleep(self.unfollow_timeout)

            return unfollowed
        except:
            pass

    def Like(self,media_url): #feed timeline or video_view or photo_view
        try:
            media_id = self.GetMediaId(media_url)
            result = self.api.post_like(media_id)
            if 'status' in result:
                if result['status'] == 'ok':
                    self.PrintText('LIKED',media_id,Fore.GREEN,Fore.GREEN)
                    with open('Data/[Just Like]/results.txt','a') as f:
                        f.write('LIKED {0} | URL: {1}'.format(media_id,media_url))
            else:
                self.PrintText('ERROR','SOMETHING WENT WRONG',Fore.RED,Fore.RED)
        except:
            pass

    def UnLike(self,media_url): #feed timeline or video_view or photo_view
        try:
            media_id = self.GetMediaId(media_url)
            result = self.api.delete_like(media_id)
            if 'status' in result:
                if result['status'] == 'ok':
                    self.PrintText('UNLIKED',media_id,Fore.GREEN,Fore.GREEN)
                    with open('Data/[Just Unlike]/results.txt','a') as f:
                        f.write('UNLIKED {0} | URL: {1}'.format(media_id,media_url))
            else:
                self.PrintText('ERROR','SOMETHING WENT WRONG',Fore.RED,Fore.RED)
        except:
            pass

    def LikeBot(self,media_url):
        if self.likebot_option == 1:
            self.Like(media_url)
            if self.likebot_timeout > 0:
                time.sleep(self.likebot_timeout)
            self.UnLike(media_url)
        else:
            self.UnLike(media_url)
            if self.likebot_timeout > 0:
                time.sleep(self.likebot_timeout)
            self.Like(media_url)

    def Comment(self,media_url):
        try:
            mediaid = self.GetMediaId(media_url)
            comment = self.PrintInput('COMMENT','Comment message',Fore.MAGENTA,Fore.WHITE,Fore.MAGENTA)
            #timeout = self.PrintInput('TIMEOUT','Enter the timeout after comments',Fore.MAGENTA,Fore.WHITE,Fore.MAGENTA)
            result = self.api.post_comment(mediaid,comment)

            if 'comment' in result:
                if result['comment']['status'] == 'Active':
                    self.PrintText('COMMENTED',comment,Fore.GREEN,Fore.GREEN)
                    with open('Data/[Comment Bot]/results.txt','a') as f:
                        f.write('COMMENTED {0} TO {1}\n'.format(comment,media_url))
            else:
                self.PrintText('ERROR','SOMETHING WENT WRONG',Fore.RED,Fore.RED)

            if self.comment_timeout > 0:
                time.sleep(self.comment_timeout)
        except:
            pass

    def FollowByHashtag(self):
        try:
            uuid = self.api.generate_uuid()

            hashtag = self.PrintInput('TAG','#',Fore.MAGENTA,Fore.WHITE,Fore.MAGENTA)

            results = self.api.feed_tag(hashtag,uuid)
        
            #print(results)
            
            items = [item for item in results.get('ranked_items', [])
                if item.get('user')]

            
            for item in items:
                #userid item['user']['pk']
                userid = item['user']['pk']
                if self.FollowById(userid) == 1:
                    self.PrintText('FOLLOWED',userid,Fore.GREEN,Fore.GREEN)
                elif self.FollowById(userid) == 2:
                    self.PrintText('ALREADY FOLLOWED',userid,Fore.RED,Fore.RED)
                else:
                    self.PrintText('ERROR','SOMETHING WENT WRONG',Fore.RED,Fore.RED)
        except:
            pass
        
    #def DeclineFollowRequestById(self,userid): #result not returns values so need to check somehow if it is worked or not
    #   result = self.api.ignore_user(userid)
    #    if 'status' in result:
    #        if result['status'] == 'ok':
    #            self.PrintText('FOLLOW REQUEST DECLINED',userid,Fore.GREEN,Fore.GREEN)
    #        else:
    #            self.PrintText('FOLLOW REQUEST CAN NOT BE DECLINED',userid,Fore.RED,Fore.RED)
    #    else:
    #        self.PrintText('ERROR','SOMETHING WENT WRONG',Fore.RED,Fore.RED)

    #    if self.decline_follow_requests_timeout > 0:
    #        time.sleep(self.decline_follow_requests_timeout)

    #def DeclineFollowRequest(self,username):
    #    userid = self.GetUserId(username)
    #    result = self.api.ignore_user(userid)
    #    self.PrintText('FOLLOW REQUEST DECLINED',username,Fore.GREEN,Fore.GREEN)
    #    if self.decline_follow_requests_timeout > 0:
    #        time.sleep(self.decline_follow_requests_timeout)

    def UnFollowByHashtag(self):
        try:
            uuid = self.api.generate_uuid()
            hashtag = self.PrintInput('TAG','#',Fore.MAGENTA,Fore.WHITE,Fore.MAGENTA)

            results = self.api.feed_tag(hashtag,uuid)
        
            #print(results)
            
            items = [item for item in results.get('ranked_items', [])
                if item.get('user')]

            
            for item in items:
                #userid item['user']['pk']
                userid = item['user']['pk']
                if self.UnfollowById(userid) == 1:
                    self.PrintText('UNFOLLOWED',userid,Fore.GREEN,Fore.GREEN)
                elif self.UnfollowById(userid) == 2:
                    self.PrintText('ALREADY UNFOLLOWED',userid,Fore.RED,Fore.RED)
                else:
                    self.PrintText('ERROR','SOMETHING WENT WRONG',Fore.RED,Fore.RED)
        except:
            pass

    def DownloadVideoOrImage(self):
        try:
            media_url = self.PrintInput('VIDEO / IMAGE','Url',Fore.MAGENTA,Fore.WHITE,Fore.MAGENTA)
            response = requests.get(media_url).text
            soup = BeautifulSoup(response,'html.parser')
            filename = ''.join(random.choice(string.ascii_letters) for len in range(0,6))
            if 'og:video' in response:
                video_url = soup.find('meta',{'property':'og:video'})
                response = requests.get(video_url['content'])
                with open('Data/[Downloads]/{0}.mp4'.format(filename),'wb') as f:
                    f.write(response.content)
                with open('Data/[Downloads]/video_download_links.txt','a') as f:
                    f.write(video_url['content']+'\n')
                self.PrintText('DOWNLOADED',filename+'.mp4',Fore.GREEN,Fore.GREEN)
            elif 'og:image' in response:
                image_url = soup.find('meta',{'property':'og:image'})
                response = requests.get(image_url['content'])
                with open('Data/[Downloads]/{0}.jpg'.format(filename),'wb') as f:
                    f.write(response.content)
                with open('Data/[Downloads]/image_download_links.txt','a') as f:
                    f.write(image_url['content']+'\n')
                self.PrintText('DOWNLOADED',filename+'.jpg',Fore.GREEN,Fore.GREEN)
            else:
                self.PrintText('ERROR','SOMETHING WENT WRONG',Fore.RED,Fore.RED)
        except:
            pass

    def DownloadVideosOrImages(self,media_url):
        try:
            response = requests.get(media_url).text
            soup = BeautifulSoup(response,'html.parser')
            filename = ''.join(random.choice(string.ascii_letters) for len in range(0,6))
            if 'og:video' in response:
                video_url = soup.find('meta',{'property':'og:video'})
                response = requests.get(video_url['content'])
                with open('Data/[Downloads]/{0}.mp4'.format(filename),'wb') as f:
                    f.write(response.content)
                with open('Data/[Downloads]/video_download_links.txt','a') as f:
                    f.write(video_url['content']+'\n')
                self.PrintText('DOWNLOADED',filename+'.mp4',Fore.GREEN,Fore.GREEN)
            elif 'og:image' in response:
                image_url = soup.find('meta',{'property':'og:image'})
                response = requests.get(image_url['content'])
                with open('Data/[Downloads]/{0}.jpg'.format(filename),'wb') as f:
                    f.write(response.content)
                with open('Data/[Downloads]/image_download_links.txt','a') as f:
                    f.write(image_url['content']+'\n')
                self.PrintText('DOWNLOADED',filename+'.jpg',Fore.GREEN,Fore.GREEN)
            else:
                self.PrintText('ERROR','SOMETHING WENT WRONG',Fore.RED,Fore.RED)
            
            if self.download_videos_or_images_timeout > 0:
                time.sleep(self.download_videos_or_images_timeout)
        except:
            pass

    def DownloadAvatar(self):
        try:
            username = self.PrintInput('TARGET','Username',Fore.MAGENTA,Fore.WHITE,Fore.MAGENTA)

            if '@' in username:
                username = username.replace('@','')

            response = requests.get('https://www.instagram.com/{0}/'.format(username)).text
            soup = BeautifulSoup(response,'html.parser')
            filename = ''.join(random.choice(string.ascii_letters) for len in range(0,6))
            if 'og:image' in response:
                image_url = soup.find('meta',{'property':'og:image'})
                response = requests.get(image_url['content'])
                with open('Data/[Grab Avatars]/{0}.jpg'.format(filename),'wb') as f:
                    f.write(response.content)
                with open('Data/[Downloads]/image_download_links.txt','a') as f:
                    f.write(image_url['content']+'\n')
                self.PrintText('DOWNLOADED',filename+'.jpg',Fore.GREEN,Fore.GREEN)
            else:
                self.PrintText('ERROR','SOMETHING WENT WRONG',Fore.RED,Fore.RED)
        except:
            pass

    def DownloadAvatars(self,username):
        try:
            if '@' in username:
                username = username.replace('@','')

            response = requests.get('https://www.instagram.com/{0}/'.format(username)).text
            soup = BeautifulSoup(response,'html.parser')
            filename = ''.join(random.choice(string.ascii_letters) for len in range(0,6))
            if 'og:image' in response:
                image_url = soup.find('meta',{'property':'og:image'})
                response = requests.get(image_url['content'])
                with open('Data/[Grab Avatars]/{0}.jpg'.format(filename),'wb') as f:
                    f.write(response.content)
                with open('Data/[Downloads]/image_download_links.txt','a') as f:
                    f.write(image_url['content']+'\n')
                self.PrintText('DOWNLOADED',filename+'.jpg',Fore.GREEN,Fore.GREEN)
            else:
                self.PrintText('ERROR','SOMETHING WENT WRONG',Fore.RED,Fore.RED)
        except:
            pass

    def FollowBot(self,username):
        if self.followbot_option == 1:
            self.Follow(username)
            if self.followbot_timeout > 0:
                time.sleep(self.followbot_timeout)
            self.UnFollow(username)
        else:
            self.UnFollow(username)
            if self.followbot_timeout > 0:
                time.sleep(self.followbot_timeout)
            self.Follow(username)

    def GetRandomProxy(self):
        proxies_file = self.ReadFile('Data/proxies.txt','r')
        proxies = {
            "http":"http://{0}".format(random.choice(proxies_file)),
            "https":"https://{0}".format(random.choice(proxies_file))
            }
        return proxies

    def UsernameChecker(self,username):
        try:
            response = ''
            if self.username_checker_use_proxies == 1:
                response = requests.get('https://www.instagram.com/{0}/'.format(username),proxies=self.GetRandomProxy())
            else:
                response = requests.get('https://www.instagram.com/{0}/'.format(username))

            if response.status_code == 200:
                self.PrintText('TAKEN',username,Fore.RED,Fore.RED)
                with open('Data/[Username Checker]/taken.txt','a') as f:
                    f.write(username+'\n')
            elif response.status_code == 404:
                self.PrintText('AVAILABLE',username,Fore.GREEN,Fore.GREEN)
                with open('Data/[Username Checker]/available.txt','a') as f:
                    f.write(username+'\n')
            else:
                self.PrintText("RATELIMITED","IF YOU DON'T USE PROXIES EXIT AND ENABLE THEM",Fore.RED,Fore.RED)
                self.UsernameChecker(username)

            if self.username_checker_timeout > 0:
                time.sleep(self.username_checker_timeout)
        except:
            self.UsernameChecker(username)


    def StoryViewer(self,username):
        try:
            userids = []
            userids.append(self.GetUserId(username))
            reels = self.api.reels_media(userids)
            result = self.api.media_seen(reels)

            if 'status' in result:
                if result['status'] == 'ok':
                    self.PrintText('STORY VIEWED',username,Fore.GREEN,Fore.GREEN)
                    with open('Data/[Stories Viewer]/results.txt','a') as f:
                        f.write('STORY VIEWED {0}\n'.format(username))
                else:
                    self.PrintText('FAILED TO VIEW STORY',username,Fore.RED,Fore.RED)
                    with open('Data/[Stories Viewer]/results.txt','a') as f:
                        f.write('FAILED TO VIEW STORY {0}\n'.format(username))
            else:
                self.PrintText('ERROR','SOMETHING WENT WRONG',Fore.RED,Fore.RED)
        except:
            pass

    def GetInstaFollowersNum(self,username):
        try:
            response = requests.get('https://www.instagram.com/{0}/?__a=1'.format(username)).text
            json_data = json.loads(response)
            if 'graphql' in json_data:
                return json_data['graphql']['user']['edge_followed_by']['count']
            else:
                return 'CANNOT GET FOLLOWERS NUM'
        except:
            pass

    def UsernameScrape(self):
        try:
            uuid = self.api.generate_uuid()
            hashtag = self.PrintInput('TAGFEED','Enter a tag to scrape from',Fore.MAGENTA,Fore.WHITE,Fore.MAGENTA)
            print('')
            results = self.api.feed_tag(hashtag,uuid)
            items = [item for item in results.get('ranked_items', [])
                if item.get('user')]

            counter = 0
            for item in items:
                counter = counter+1
                username = '@'+item['user']['username']
                self.PrintText(counter,'{0}'.format(username),Fore.GREEN,Fore.GREEN)
                with open('Data/[Username Scraper]/scraped.txt','a') as f:
                    f.write(username+'\n')
        except:
            pass
        

    def AccountChecker(self,combos):
        try:
            link = 'https://www.instagram.com/accounts/login/'
            login_url = 'https://www.instagram.com/accounts/login/ajax/'

            curtime = int(datetime.now().timestamp())

            get_headers = {
                "cookie": "ig_cb=1" #if this cookie header is missing you will receive cookie errors
            }

            response = requests.get(link,headers=get_headers)

            csrf = response.cookies['csrftoken']

            payload = {
                'username': combos.split('.')[0],
                'enc_password': '#PWD_INSTAGRAM_BROWSER:0:{0}:{1}'.format(curtime,combos.split(':')[-1]),
                'queryParams': {},
                'optIntoOneTap': 'false'
            }

            login_header = {
                "User-Agent": "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36",
                "X-Requested-With": "XMLHttpRequest",
                "Referer": "https://www.instagram.com/accounts/login/",
                "x-csrftoken": csrf
            }

            login_response = ''

            if self.account_checker_use_proxies == 1:
                login_response = requests.post(login_url, data=payload, headers=login_header,proxies=self.GetRandomProxy())
            else:
                login_response = requests.post(login_url, data=payload, headers=login_header)

            json_data = json.loads(login_response.text)

            if 'authenticated' in json_data:
                if json_data['authenticated'] == True:
                    followers = self.GetInstaFollowersNum(combos.split(':')[0])
                    self.PrintText('HIT','{0}:{1} FOLLOWERS: {2}'.format(combos.split(':'),combos.split(':')[-1],followers),Fore.GREEN,Fore.GREEN)
                    with open('Data/[Account Checker]/hits.txt','a') as f:
                        f.write('{0}:{1}\n'.format(combos.split(':')[0],combos.split(':')[-1]))
                    with open('Data/[Account Checker]/detailed_hits.txt','a') as f:
                        f.write('{0}:{1} FOLLOWERS: {2}'.format(combos.split(':')[0],combos.split(':')[-1],followers))
                else:
                    self.PrintText('BAD','{0}:{1}'.format(combos.split(':')[0],combos.split(':')[-1]),Fore.RED,Fore.RED)
                    with open('Data/[Account Checker]/bads.txt','a') as f:
                        f.write('{0}:{1}\n'.format(combos.split('.')[0],combos.split(':')[-1]))
            else:
                self.PrintText('ERROR','{0}:{1} -> {2}'.format(combos.split(':')[0],combos.split(':')[-1],json_data['message']),Fore.RED,Fore.RED)

            if self.account_checker_timeout > 0:
                time.sleep(self.account_checker_timeout)
        except:
            self.AccountChecker(combos)

if __name__ == '__main__':
    main = Main()
    main.Menu()