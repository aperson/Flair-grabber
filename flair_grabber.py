#/usr/bin/env python3

import json, httplib2, random, signal, sys, time
from urllib.parse import urlencode

def sigint_handler(signal, frame):
    '''Handles ^c'''
    print('Recieved SIGINT! Exiting...')
    sys.exit(0)

class Redditor:
    def __init__(self, username, password, sleep=2):
        self.headers = {'Content-type' : 'application/x-www-form-urlencoded; charset=UTF-8'}
        self.username = username
        self.password = password
        self.sleep = sleep
        self.login(self.username, self.password)
    
    def _request(self, url, method='GET', body=''):
        '''Essentially wraps the httplib2.Http.request and saves us from throwing
        time.sleep(self.sleep) everywhere.  Will eventually handle some some errors.  Oh, and we
        urlencode the body here, so don't bother doing it elsewhere.'''
        http = httplib2.Http('.cache', timeout=30)
        if body:
            body['api_type'] = 'json'
            body = urlencode(body)
        
        resp, cont = http.request(url, method, headers=self.headers, body=body)
        
        if resp.status == 200:
            time.sleep(self.sleep) # I know it makes more sense to sleep after the request, but meh
            return resp, json.loads(cont.decode('utf-8'))
    
    def login(self, username, password):
        '''Logs into reddit.  Sets the appropriate http headers and the modhash.This is called on
        class initialization.'''
        body = {'user' : username, 'passwd' : password}
        resp, cont = self._request('https://www.reddit.com/api/login', 'POST', body)
        
        self.headers['Cookie'] = resp['set-cookie']
        self.modhash = cont['json']['data']['modhash']
    
    def flairlist(self, r, limit=1000, after='', before=''):
        '''Returns a dict of the json from the flairlist api call.  Usage is the same as documented,
        sans the need for the modhash.'''
        body = urlencode({'r' : r, 'limit' : limit, 'after' : after,
                'before' : before, 'uh' : self.modhash})
        # I should probably just cut out the httplib2 stuff and use urllib
        # Something about the normal GET requests I can't get working, so we're hacking it a bit
        resp, cont = self._request(
            'http://www.reddit.com/r/{}/api/flairlist.json?{}'.format(r, body), 'GET')
        
        return cont
    
    def all_flairlist(self, subreddit):
        '''Currently, we're only concerned about the flair class and not the flair text.
        returns a dict of {'flair-class' : ['username', ], }.'''
        flair_list = dict()
        flair_count = 0
        page_count = 1
        start_time = time.time()
        last_time = time.time()
        print('Grabbing first page of flairs for /r/{}.'.format(subreddit))
        flair_page = self.flairlist(subreddit)
        
        if 'next' in flair_page:
            while True:
                for i in flair_page['users']:
                    if i['flair_css_class'] not in flair_list:
                        flair_list[i['flair_css_class']] = []
                    
                    flair_list[i['flair_css_class']].append(i['user'])
                    flair_count += 1
                    last_time = time.time()
                if 'next' in flair_page:
                    print('Grabbing page {}.'.format(flair_page['next']))
                    flair_page = self.flairlist(subreddit, after=flair_page['next'])
                else:
                    break
                
                print('{} flairs processed in {:.2f} seconds.'.format(flair_count,
                    time.time() - last_time))
                page_count += 1
                last_time = time.time()
                
        else:
            for i in flair_page['users']:
                if i['flair_css_class'] not in flair_list:
                    flair_list[i['flair_css_class']] = []
                
                flair_list[i['flair_css_class']].append(i['user'])
                flair_count += 1
            
        print('{} flairs processed in {:.2f} seconds across {} pages.'.format(flair_count,
            time.time() - start_time, page_count))
        return flair_list

def piechart(data, title=None, colors=None, size='600x400'):
    '''Accepts a dictionary of label:value  Optionally accepts the title and colors.'''
    baseurl = 'https://chart.googleapis.com/chart?cht=p'
    chs = 'chs={}'.format(size)
    chd = 'chd=t:{}'.format(','.join([str(data[i]) for i in data]))
    chl = 'chl={}'.format('|'.join(['{}:{}'.format(i, data[i]) for i in data]))
    chds = 'chds=0,{}'.format(sum(data[i] for i in data))
    if title:
        chtt = 'chtt={}'.format(title.replace(' ', '+').replace('/n', '|'))
    else:
        chtt = None
    if colors:
        if type(colors) == str:
            chco = 'chco={}'.format(colors)
        elif len(colors) == 2:
            chco = 'chco={}'.format(','.join(colors))
        else:
            chco = 'chco={}'.format('|'.join(colors))
    else:
        chco = 'chco={}'.format('|'.join(
            hex(random.randint(0, 16777215))[2:].upper().zfill(6) for i in range(len(data))))
    output = []
    for i in baseurl, chs, chd, chds, chtt, chl, chco:
        if i:
            output.append(i)
    return '&'.join(output)

def minecraft_charts(minecraftflair):
    '''Builds the charts for /r/minecraft's mob flair.  This is sorta specific to that subreddit, so
    don't expect this to work for any other sub.'''
    sheep = '''sheep lightgraysheep graysheep blacksheep brownsheep pinksheep redsheep orangesheep \
    yellowsheep limesheep greensheep lightbluesheep cyansheep bluesheep purplesheep magentasheep \
    '''.split()
    cows = '''cow mooshroom'''.split()
    people = '''steve testificate'''.split()
    slimes = '''slime magmacube'''.split()
    spiders = '''cavespider spider'''.split()
    passive = sheep + cows + ['testificate']
    neutral = '''enderman wolf zombiepigman'''.split()
    aggressive = '''blaze creeper enderdragon ghast magmacube silverfish skeleton slime \
    zombie'''.split() + slimes + spiders
    overworld = '''chicken enderman pig squid testificate creeper silverfish skeleton slime \
    wolf zombie'''.split() + sheep + spiders
    nether = '''zombiepigman blaze ghast magmacube'''.split()
    end = '''enderman enderdragon'''.split()
    everything = passive + neutral + aggressive
    categories = {'sheep' : sheep, 'cows' : cows, 'people' : people, 'slimes' : slimes,
    'spiders' : spiders, 'passive' : passive, 'neutral' : neutral, 'aggressive' : aggressive,
    'overworld' : overworld, 'nether' : nether, 'end' : end}
    sheep_colors = {'white' : 'd6d6d6', 'lightgray' : 'c3c3c3', 'gray' : '7f7f7f',
    'black' : '000000', 'brown' : 'b97a57', 'pink' : 'ffaec9', 'red' : 'ff5555',
    'orange' : 'ff7f27', 'yellow' : 'ffc90e', 'lime' : 'b5e61d', 'green' : '22b14c',
    'lightblue' : '99d9ea', 'cyan' : '00a2e8', 'blue' : '3f48cc', 'purple' : 'b962b9',
    'magenta' : 'cc82ba'}
    labels = {'sheep' : 'Colors of Sheep', 'cows': 'Favorite Cow',
    'people' : 'Steve or Testificate?', 'slimes' : 'Slime or Magma Cube?', 
    'spiders' : 'Spider or Cave Spider?', 'passive' : 'Favorite Passive Mob', 
    'neutral' : 'Favorite Neutral Mob', 'aggressive' : 'Favorite Aggressive Mob',
    'overworld' : 'Favorite Overworld Mob', 'nether' : 'Favorite Nether Mob',
    'end' : 'Favorite End Mob'}
    results = dict()
    for c in categories:
        results[c] = {i : len(minecraftflair[i]) for i in categories[c]}
        if c == 'sheep':
            for i in results[c].copy():
                if i == 'sheep':
                    results[c]['white'] = results[c].pop(i)
                else:
                    results[c][i[:-5]] = results[c].pop(i)
            print('{}: {}'.format(c, piechart(results[c], labels[c], \
            [sheep_colors[i] for i in results[c]])))
        else:
            if 'sheep' in results[c]:
                sheeps = 0
                for i in results[c].copy():
                    if i.endswith('sheep'):
                        sheeps += results[c].pop(i)
                results[c]['sheep'] = sheeps
            print('{}: {}'.format(c, piechart(results[c], labels[c])))
            
       


if __name__ == '__main__':
    signal.signal(signal.SIGINT, sigint_handler)
    args = sys.argv[1:]
    if len(args) >=3:
        user = Redditor(args[0], args[1])
        for i in args[2:]:
            output = user.all_flairlist(i)
            print('Summary of flair for /r/{}:'.format(i))
            for o in output:
                print('{}: {}'.format(o, len(output[o])))
            with open('{}.json'.format(i), 'wt') as f:
                f.write(json.dumps(output))
                print('Wrote {}.json to file.'.format(i))
    else:
        print('Incorrect number of arguments.\nTakes: username password subreddit [subreddits]')
