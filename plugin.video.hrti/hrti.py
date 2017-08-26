import sys
import urllib
import urlparse
import json
import requests

import xbmcgui
import xbmcplugin
import xbmcaddon


'''
this is the catalog we navigate

{
	"categories": [{
			"id": "5",
			"name": "Home",
			"description": "",
			"thumbnail": "https:\/\/hrti-static.hrt.hr\/rev-1484128327\/spectarAdmin\/images\/no_thumbnail.jpg",
			"parent_id": 0,
			"url": "{vsc}\/category_id\/5",
			"display_subcategories": false,
			"uriid": ""
		},
        
'''

#URIs as observed from hrti.hr
'''
base_uri = "https://hrti-static.hrt.hr/client_api.php"        

catalog_uri = base_uri+'/vod_catalog/structure/language/hr/application_id/all_in_one'
category_uri= base_uri+"/vod_catalog/search/language/hr/application_id/all_in_one/category_id/{category_id}/alternatives/true/format/json"
playlist_url ="https://prd-hrt.spectar.tv/player/get_smil/id/{video_id}/video_id/{video_id}/token/{token}/token_expiration/{token_expiration}/asset_type/Movie/playlist_template/nginx/channel_name/{channel_name}/playlist.m3u8?foo=bar"
        
img_url = base_uri+"/image/transform/tasks/thumbnail_fix/width/{width}/height/{height}/format/thumbnail/video_id/{video_id}/img_compression/{compression}"
'''        

        
        
def display_categories(parent_id, settings, addon_handle):
    '''
    This is the 1st listing level, showing root menu and submenus for categories
    this does NOT show episodes - actual videos
    In addition to parsing loaded json data
    this method has additional SEARCH pseudo menu item
    '''
    
    #simple caching for catalog file, to be loaded only once at addon load instead of at every category listing
    catalog_file = xbmc.translatePath("special://profile/hrti_catalog.json")
    #print catalog_file
    
    if not parent_id:
        #reload the catalog from hrti 
        cat = urllib.urlopen(settings['catalog_uri'])
        data = cat.read()
        catjs = json.loads(data)
        
        #write to local file for subcategories not to reload it from network
        with open(catalog_file, 'w') as f:
            f.write(data)
            
        parent_id = 0 #int for zero and string for others
    else:
        #load json from local file
        with open(catalog_file, 'r') as f:
            catjs = json.load(f)
            
        parent_id = parent_id[0]
        

    display_cats = [c for c in catjs['categories'] if c['parent_id']==parent_id]
    
    #if parent id is zero, skip the root category (we implicitly know it is only one) and reload its subcats
    if len(display_cats)==1 and parent_id==0:
        parent_id = display_cats[0]['id']
        display_cats = [c for c in catjs['categories'] if c['parent_id']==parent_id]
        
        #TBD once kodi supports DASH mpd format kodi 17, NOT SO FAST
        #live_cat = {'name': 'UZIVO', 'id':'live', 'display_subcategories':True, 'thumbnail':''}
        #display_cats.append(live_cat)
        
        #this being the root menu, add the search dialog item
        search_cat = {'name': 'PRETRAGA', 'id':'search', 'display_subcategories':True, 'thumbnail':''}
        display_cats.append(search_cat)
        
        #add the search history category
        search_history_cat = {'name': 'POVIJEST PRETRAGA', 'id':'search_history', 'display_subcategories':True, 'thumbnail':''}
        display_cats.append(search_history_cat)

        #ALSO ADD THE LIVE TV CATEGORIES
        '''
        Categories 
        https://prd-hrt-live.morescreens.com/OIV_HRT1_TV/manifest.mpd?video_id=83&authority_instance_id=spectar-prd-hrt&token=nAAsWBFxkJnzA_-nF7JF4g&token_expiration=1485194499&profile_id=99999&application_installation_id=6364871&subscriber_id=99999&application_id=all_in_one&channel_name=hrt1
        
        This is MPD aka DASH manifest, Kodi 17 will support it: https://github.com/peak3d/inputstream.mpd
        
        live playlist requires RepresentationID and Time
        for example: https://prd-hrt-live.morescreens.com/OIV_HRT1_TV/2017-01-28/14/chunk_ue27le28m_ctvideo_cfm4s_ridp0a0r4_cinit_mpd.m4s
        
        <Representation id="p0a0r0
         <SegmentTemplate timescale="90000" media="2017-01-28/14/chunk_ue27le28m_ctvideo_cfm4s_rid$RepresentationID$_cs$Time$_mpd.m4s" initialization="2017-01-28/14/chunk_ue27le28m_ctvideo_cfm4s_rid$RepresentationID$_cinit_mpd.m4s">
       
        '''
        
    
        
        
    
        
    
    #check if there are any subcategories to show, otherwise assume this category contains episodes only
    if display_cats:
    
        xbmcplugin.setContent(addon_handle, 'videos')
        
        for cat in display_cats:
            name = cat['name'].encode('utf-8')
            url = sys.argv[0]+"?"+urllib.urlencode([('parent_id', cat['id']), ('foldername', name), ('display_subcategories', cat['display_subcategories'])])
            li = xbmcgui.ListItem(name, iconImage=cat['thumbnail'])
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,listitem=li, isFolder=True)
            
        xbmcplugin.endOfDirectory(addon_handle)
        
    else:
    	uri = None
        if parent_id=='search':
            #PSEUDO MENU, SEARCH, SHOWING AT ROOT ONLY
            dialog = xbmcgui.Dialog()
            search = dialog.input('Naslov ili dio naslova video ili audio zapisa', type=xbmcgui.INPUT_ALPHANUM)
            
            print "Search:{}".format(search)
            
            if search and search!="":
                searchHistory = xbmcaddon.Addon().getSetting('search_history')
                searchHistory = json.loads(searchHistory) if searchHistory else []
                if search not in searchHistory:
                    searchHistory.append(search)
                    xbmcaddon.Addon().setSetting('search_history', json.dumps(searchHistory))
    
                uri = settings['search_uri'].format(search_string=search)

        elif parent_id=='search_history':
            dialog = xbmcgui.Dialog()
        	
            searchHistory = xbmcaddon.Addon().getSetting('search_history')
            searchHistory = json.loads(searchHistory) if searchHistory else []

            i = dialog.select("Povijest pretraga", searchHistory)
            if i>=0:
	            search = searchHistory[i]
	            
	            print 'Povijest pretraga:{}'.format(i)
	            uri = settings['search_uri'].format(search_string=search)
        	
        elif parent_id=='live':
            #LIVE CATEGORIES
            uri = settings['live_uri']
        else:
            #ALL OTHER, ONDEMAND CATS
            uri = settings['category_uri'].format(category_id=parent_id)


        if uri:    
            r = urllib.urlopen(uri)
            cat = json.loads(r.read());
            print uri
         	#print json.dumps(episodes, indent=2)

            if parent_id=='live':
                display_live(cat, settings, addon_handle)
            else:
                display_episodes(cat, settings, addon_handle)
            
            
    return
        
        

'''
opens the session with auth site
authenticates and returns the auth token
for further video streams

thanks to plugin.video.croatia_od for original sources
@returns token,expiration,subscriber_id,profile_id
'''        
def get_token(settings):

    if not (settings['username'] and settings['password']):
        dialog = xbmcgui.Dialog()
        dialog.ok("Authentication Failed", 'In order to view episodes, please enter the HRTi username and password under this addon Configure menu.')
        return 'x','x'
        
    session=requests.Session()
    headers={}
    cookies=session.cookies
    #headers['cookies']=cookies
    headers['User-agent']="XBMC plugin.video.hrti/1.0"

    resp_data = session.post(settings['uuid_uri'], data = '{"application_publication_id":"all_in_one"}' , headers=headers).content
    data=json.loads(resp_data)

    uuid = data['uuid']

    put_data = '{"application_publication_id":"all_in_one","uuid":"%s","screen_height":1080,"screen_width":1920,"os":"Windows","os_version":"NT 4.0","device_model_string_id":"chrome 42.0.2311.135","application_version":"1.1"}'%uuid
    resp_data = session.put(settings['uuid_uri'], data = put_data , headers=headers).text
    data=json.loads(resp_data)

    session_id = data['session_id']

    login_data = '{"username":"%s","password": "%s"}'%(settings['username'], settings['password'])
    login_url = settings['login_uri'].format(session_id=session_id)

    resp = session.post(login_url, data = login_data, headers = headers)
    data = json.loads(resp.text)
    print "Session data: "
    print data
    
    try:
        session_token = data['session_token']
    except:
        dialog = xbmcgui.Dialog()
        dialog.ok("Authentication Failed", 'Authentication to HRTi failed. Please verify the HRTi username and password uder this addon Configure menu')
        return 'x','x'

    stream_token = data.get('secure_streaming_token')
    str_token = stream_token.split('/')[0]
    expire = stream_token.split('/')[-1]
    
    subscriber_id = data.get('subscriber_id')
    profile_id = data.get('id')

    return str_token,expire,subscriber_id,profile_id


def display_live(channels, settings, addon_handle):
    '''
    list all live channels 
    '''
    
    #this will pop up the warning if user/pass not set
    token, token_expiration, subscriber_id, profile_id = get_token(settings)
    
    
    for c in channels:
        #  <setting id="live_mpd" visible="false" default="https://prd-hrt-live.morescreens.com/{external_id}/manifest.mpd?video_id={video_id}&authority_instance_id=spectar-prd-hrt&token={token}&token_expiration={token_expiration}&profile_id={profile_id}&application_installation_id={application_installation_id}&subscriber_id={subscriber_id}&application_id=all_in_one&channel_name={channel_name}"/>
        #GOOD ONE FROM BROWSER: <source src="https://prd-hrt-live-2.spectar.tv/OIV_HRT1_TV/manifest.mpd?video_id=83&amp;authority_instance_id=spectar-prd-hrt&amp;token=nAAsWBFxkJnzA_-nF7JF4g&amp;token_expiration=1485194499&amp;profile_id=99999&amp;application_installation_id=6364871&amp;subscriber_id=99999&amp;application_id=all_in_one&amp;channel_name=hrt1" type="application/dash+xml">
        #https://prd-hrt-live.morescreens.com/OIV_HRT2_TV/manifest.mpd?video_id=87&authority_instance_id=spectar-prd-hrt&token=TUtrC_xuO5qL9H6Omcn2kw&token_expiration=1489934776&profile_id=TBD&application_installation_id=TBD&subscriber_id=TBD&application_id=all_in_one&channel_name=HRT2
        #failing https://prd-hrt-live-2.spectar.tv/OIV_HRT1_TV/manifest.mpd?video_id=83&authority_instance_id=spectar-prd-hrt&token=5cm4RsB80J73RfvWCzicuw&token_expiration=1489936228&profile_id=99999&application_installation_id=6364871&subscriber_id=99999&application_id=all_in_one&channel_name=HRT1
        
        #TBD get it from somewhere
        application_installation_id=0
        
        
        url = settings['live_mpd'].format(video_id=c['id'], token=token, token_expiration=token_expiration, external_id=c['external_id'], channel_name=c['name'], profile_id=profile_id, application_installation_id=application_installation_id, application_id='all_in_one', subscriber_id=subscriber_id)
        
        #url = settings['live_mpd_test'].format(video_id=c['id'], token=token, token_expiration=token_expiration, external_id=c['external_id'], channel_name=c['name'])
        #url='https://prd-hrt-live.morescreens.com/OIV_HRT2_TV/manifest.mpd'
                
        li = xbmcgui.ListItem(c['name'], iconImage=c['img'])
        #li.addStreamInfo(
        
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=False)
        
        
    
    xbmcplugin.endOfDirectory(addon_handle)
    
    return
    
    
    


def display_episodes(cat, settings, addon_handle):
    '''
    list all video on demand episodes found in cat category json file
    '''
    
    #this will pop up the warning if user/pass not set
    token, token_expiration, _subscriber_id, _profile_id = get_token(settings)
    
    try:
        episodes = cat['video_listings'][0]['alternatives'][0]['list']
        videos = cat['videos']
    except:
        episodes = [] #simple key error ignore
    
    for episode_id in episodes:
    
        for video in videos:
            if video['id'] == episode_id:
                        
                title = video['title']['title_long']
                title = title.encode('utf-8')
                        #>>> video['title']['title_long']
                        #u'CRNO-BIJELI SVIJET: Zagreb je hladan grad, serija (11/12) (HD)'
                        #print("episodes(), found title: {}".format(title))
                        
                        #https://prd-hrt.spectar.tv/player/get_smil/id/2998391/video_id/2998391/token/j5sdF_yZLbjzyaYkBRQl4Q/token_expiration/1483984596/asset_type/Movie/playlist_template/nginx/channel_name/crnobijeli_svijet_ljudi_samoe_2._sezona_1212_hd/playlist.m3u8?foo=bar"

                        
                img=settings['img_uri'].format(width=800,height=600,video_id=episode_id,compression=60)
                        
                        
                #converting the video title to url path component 'channel_name' as observed at site, unsure of exact regex syntax used
                channel_name = unicode(title, errors='ignore') #removing nonascii
                #dumb regex
                channel_name = channel_name.lower().replace(" ","_").replace('-','').replace(':_','_').replace('(','').replace(')','').replace('/','').replace("'","").replace("?",'')
                #remove leading or trailing replacements
                channel_name = channel_name.strip('_')
                
                
                url = settings['playlist_uri'].format(video_id=episode_id, token=token, token_expiration=token_expiration, channel_name=channel_name)
                        
                info={}
                info["plot"]=video['title']['summary_short']
                info["year"]=video['properties']['year']
                info["title"]=title
                info['aired']=video['properties']['broadcast_date']
                info['cast']=[]

                for actor in video['credits']['actors']:
                    info['cast'].append(actor['name'])
                
                        
                li = xbmcgui.ListItem(title, iconImage=img)
                li.setInfo("video", info)
                
                xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=False)
                
                
                break #found the episode
        
        
    
    xbmcplugin.endOfDirectory(addon_handle)



def main():
    base_url = sys.argv[0]
    addon_handle = int(sys.argv[1])
    args = urlparse.parse_qs(sys.argv[2][1:])
    
    parent_id = args.get('parent_id', None)
    
    #get config data from settings.xml, do not hardcode here
    my_addon = xbmcaddon.Addon()
    keys = ['username', 'password', 'catalog_uri', 'category_uri', 'playlist_uri','img_uri', 'login_uri', 'uuid_uri', 'search_uri', 'live_uri', 'live_mpd']
    settings = {}
    for key in keys:
        settings[key]=my_addon.getSetting(key)
    
    
    #if not parent_id:
        #debug print settings only at 1st load
        #print "settings: {}".format(json.dumps(config))
        
    display_categories(parent_id, settings, addon_handle)
    
    return
        
    
    
    
        
if __name__ == "__main__":
    print "hrti addon: {}".format(sys.argv)
    
    main()
    
