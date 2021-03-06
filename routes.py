# coding=utf-8

from mole import route, run, static_file, error, get, post, put, delete, Mole  # 均来自Mole类
from mole.template import template, Jinja2Template
from mole import request
from mole import response
from mole.mole import json_dumps
from mole import redirect
from mole.sessions import get_current_session, authenticator

from config import media_prefix
import config
import i18n

import nginx
import json
import os
import glob

import commands
import os.path, time

auth_required = authenticator(login_url='/auth/login')


@route('/%s/:file#.*#' % media_prefix)
def media(file):
    return static_file(file, root='./media')


@route('/nginx_tree')
@auth_required()
def nginx_tree():
    jsonlist = []
    # jsondict = {"id": 1, "pId": 0, "name": "nginx_conf"}
    # jsonlist.append(jsondict)
    f_id=1
    for file in os.listdir(config.nginx_conf_path):
        jsonlist.append({"id": f_id, "pId": 0, "name": file})
        # f_id=f_id+1
        c = nginx.loadf(config.nginx_conf_path+file)
        jsonlist.append({"id": int(str(f_id)+"2"), "pId": f_id, "name": "upstream"})
        jsonlist.append({"id": int(str(f_id)+"3"), "pId": f_id, "name": "servers"})
        Upstreams = c.filter(btype="Upstream")
        u_id = 0
        s_id = 0
        for i in Upstreams:
            id = int(str(f_id)+"2" + str(u_id + 1))
            jsondict = {"id": id, "pId": int(str(f_id)+"2"), "name": i.value}
            u_id = u_id + 1
            # print type(u_id),u_id
            jsonlist.append(jsondict)
        Servers = c.filter(btype="Server", name='')
        for i in Servers:
            server_name = i.filter("key", "server_name")[0].value
            id = int(str(f_id)+"3" + str(s_id + 1))
            jsondict = {"id": id, "pId": int(str(f_id)+"3"), "name": server_name}
            s_id = s_id + 1
            # print type(s_id),s_id
            jsonlist.append(jsondict)
        f_id = f_id + 1
        # mylocation = c.children
        # print Upstreams,"-----------",Servers
    return template('nginx_tree',nginx_tree=json.dumps(jsonlist),media_prefix=media_prefix)

@route('/nginxview')
@auth_required()
def nginxview():
    nginx_version_status,nginx_version=commands.getstatusoutput(config.nginx_cmd+" -v")
    configure_arguments_status,configure_arguments=commands.getstatusoutput(config.nginx_cmd+" -V")
    configure_arguments=configure_arguments.split(":")[-1]
    nginx_version=nginx_version.split(":")[1]
    last_save_time=time.ctime(os.path.getctime(config.nginx_cmd.rstrip()))
    status, stime = commands.getstatusoutput("ps -A -opid,stime,etime,args |grep /usr/local/nginx/sbin/nginx|grep -v grep|awk {'print $2'}")
    status, etime = commands.getstatusoutput("ps -A -opid,stime,etime,args |grep /usr/local/nginx/sbin/nginx|grep -v grep|awk {'print $3'}")
    return template('nginxview',
                    nginx_version=nginx_version,
                    stime=stime,
                    etime=etime,
                    last_save_time=last_save_time,
                    configure_arguments=configure_arguments,
                    media_prefix=media_prefix)


@route('/upstream_edit')
@auth_required()
def upstream_edit():
    upstream_name = request.GET.get('upstream_name', '')
    file_name = request.GET.get('file_name', '')
    path_file_name = config.nginx_conf_path + file_name
    c = nginx.loadf(path_file_name)
    u = c.filter(btype="Upstream", name=upstream_name)
    keys=u[0].keys
    rows=len(keys)
    upstream_value=""
    for i in keys:
        upstream_value= upstream_value+i.name+" "+i.value+"\r\n"
    return template('upstream_edit',upstream_name=upstream_name,upstream_value=upstream_value,path_file_name=path_file_name,rows=rows+5,media_prefix=media_prefix)


@route('/upstream_submit',method='POST')
@auth_required()
def upstream_submit():
    upstream_value=request.POST.get('upstream_value', '')
    upstream_name=request.POST.get('upstream_name', '')
    path_file_name = request.POST.get("path_file_name", "")
    c = nginx.loadf(path_file_name)
    search_upstream=c.filter(btype="Upstream", name=upstream_name)

    if len(search_upstream):
        u=search_upstream[0]
        c.remove(u)
        new_u = nginx.Upstream(upstream_name, )
        for line in upstream_value.split("\n"):
            if len(line.split(" "))>=	2:
                # print line.split(" ")
                new_u.add(nginx.Key(line.split(" ")[0], line.split(" ")[1]))

    else:
        new_u = nginx.Upstream(upstream_name, )
        for line in upstream_value.split("\n"):
            if len(line.split(" ")) >= 2:
                # print line.split(" ")
                new_u.add(nginx.Key(line.split(" ")[0], line.split(" ")[1]))
    c.add(new_u)
    nginx.dumpf(c, path_file_name)

    print type(upstream_value),path_file_name,upstream_name
    return upstream_value

@route('/server_edit')
@auth_required()
def server_edit():
    server_name = request.GET.get('server_name', '')
    file_name = request.GET.get('file_name', '')
    path_file_name=config.nginx_conf_path+file_name
    c = nginx.loadf(path_file_name)
    servers = c.filter("Server")
    for i in servers:
        if server_name==i.filter("key","server_name")[0].value:
            # print type(i),222222,server_name
            server_value = "".join(i.as_strings)
            rows=len(i.as_strings)

            # server_value=json.dumps(server_value)
            # if server_name==
    # keys=u[0].keys
    # upstream_value=""
    # for i in keys:
    #     upstream_value= upstream_value+i.name+" "+i.value+"\r\n"
    return template('server_edit',server_name=server_name,server_value=server_value,path_file_name=path_file_name,rows=rows+5,media_prefix=media_prefix)



@route('/server_submit',method='POST')
@auth_required()
def server_submit():
    server_name=request.POST.get('server_name', '')
    server_value=request.POST.get('server_value', '')
    path_file_name=request.POST.get("path_file_name","")
    c = nginx.loadf(path_file_name)
    servers = c.filter("Server")
    for i in servers:
        if server_name == i.filter("key", "server_name")[0].value:
            c.remove(i)
    new_c=nginx.loads(server_value)
    new_server=new_c.filter('Server')[0]
    c.add(new_server)
    # print "remove ok"
    # c.add(myserver)
    nginx.dumpf(c, path_file_name)
    # print myserver
    return server_value


@route('/nginx_reload')
@auth_required()
def nginx_reload():
    status, output = commands.getstatusoutput(config.nginx_cmd+"-s reload")
    print status,output
    return template('shell',status=status,output=output,media_prefix=media_prefix)

@route('/nginx_restart')
@auth_required()
def nginx_restart():
    status, output = commands.getstatusoutput(config.nginx_cmd+"-s reload")
    print status,output
    return template('shell',status=status,output=output,media_prefix=media_prefix)

@route('/nginx_check')
@auth_required()
def nginx_check():
    status, output = commands.getstatusoutput(config.nginx_cmd+"-t")
    print status,output
    return template('shell',status=status,output=output,media_prefix=media_prefix)

@route('/')
@auth_required()
def server_view():

    return template("main", media_prefix=media_prefix)


@route('/auth/login', method=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.POST.get("username", '')
        password = request.POST.get("password", '')
        if password == config.admin_pwd and username == config.admin_user:
            session = get_current_session()
            session['username'] = username
            return {'code': 0, 'msg': 'OK'}
        else:
            return {'code': -1, 'msg': '用户名或密码错误'}
    else:
        return template('auth/login.html', config=config, media_prefix=media_prefix)


@route('/auth/logout')
def logout():
    session = get_current_session()
    del session['username']
    return redirect(request.params.get('next') or '/')


if __name__ == "__main__":
    from mole.mole import default_app
    from mole.sessions import SessionMiddleware

    app = SessionMiddleware(app=default_app(), cookie_key="457rxK3w54tkKiqkfqwfoiQS@kaJSFOo8h", no_datastore=True)
    run(app=app, host=config.host, port=config.port, reloader=config.debug)
