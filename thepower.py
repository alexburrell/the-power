# To do:
#   - Make it use ajax calls


import cherrypy
import pystache
import json
from wemo.wemo import *
from pynest.nest import *


wemos = []
wemo_dict = {}
nest = Nest(username='peterhajas@gmail.com', password='byHwxFbJbrB3tRNCxG3e')
nest.login()
nest_curtemp = 0
nest_targettemp = 0
nest_method = 'cool'
renderer = pystache.Renderer()


def find_nest():
    global nest_curtemp
    global nest_targettemp
    global nest_method

    nest.get_status()
    nest_curtemp = nest.get_curtemp()
    nest_targettemp = nest.get_targettemp()
    nest_method = nest.get_method()


def find_wemos():
    global wemos
    global wemo_dict

    wemos = search()
    wemo_dict = {}
    for wemo in wemos:
        print wemo.friendlyName
        wemo_dict[wemo.friendlyName] = wemo


class ThePowerTemplate(object):
    def nest(self):
        return {
            "curtemp": '{0}&deg;F'.format(int(round(nest_curtemp))),
            "targettemp": '{0}&deg;F'.format(int(round(nest_targettemp))),
            "method": nest_method
        }

    def wemo_buttons(self):
        wemo_list = []
        if len(wemos) > 0:
            for wemo in wemos:
                wemo_list.append({
                    'name': wemo.friendlyName,
                    'classname': wemo.friendlyName.replace(' ', '-').lower(),
                    'state': 'on' if wemo.binaryState else 'off',
                    'href': 'toggle/{0}'.format(wemo.friendlyName)
                })
        return wemo_list


class Power:
    @cherrypy.expose
    def index(self):
        find_nest()
        find_wemos()

        template = ThePowerTemplate()
        return renderer.render(template)

    @cherrypy.expose
    def toggle(self, switch):
        wemo_dict[switch].binaryState = not wemo_dict[switch].binaryState
        cherrypy.response.headers['Content-Type'] = "application/json"

        state = 'on' if wemo_dict[switch].binaryState else 'off'
        return json.dumps({"state" : state})

    @cherrypy.expose
    def change_temp(self, direction):
        change = 1 if direction == "higher" else -1
        nest.set_temperature(int(round(nest_targettemp)) + change)

        find_nest()
        cherrypy.response.headers['Content-Type'] = "application/json"
        return json.dumps({
            "newTemp" : '{0}&deg;F'.format(int(round(nest_targettemp))),
            "curTemp" : '{0}&deg;F'.format(int(round(nest_curtemp)))
        })

    @cherrypy.expose
    def update(self):
        find_nest()
        find_wemos()

        template_data = ThePowerTemplate()
        cherrypy.response.headers['Content-Type'] = "application/json"
        return json.dumps({
            "nest": template_data.nest(),
            "wemo": template_data.wemo_buttons()
        })


if __name__ == "__main__":
    config = {
        '/style.css': {
            'tools.staticfile.on': True,
            'tools.staticfile.filename': 'style.css',
        },
        '/scripts.js': {
            'tools.staticfile.on': True,
            'tools.staticfile.filename': 'scripts.js'
        }
    }
    cherrypy.server.socket_host = '0.0.0.0'
    cherrypy.quickstart(Power(), "/", config=config)
