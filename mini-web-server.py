import socket
import sys
import re
import multiprocessing


# 用来记录web服务器的主路径,这个路径下存放这个所有需要的资源
STATIC_ROOT = "./static"


class WSGIServer():

    def __init__(self, port, app):
        """负责创建tcp服务器"""
        # 1. 创建tcp套接字
        self.tcp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # 2. 绑定本地信息
        self.tcp_server_socket.bind(("", port))
        # 3. 将套接字设置为监听套接字
        self.tcp_server_socket.listen(128)
        # 4. 保存app
        self.app = app

    def run_forever(self):
        """运行web服务器"""
        while True:
            # 4. 等待一个客户端的链接
            client_socket, client_addr = self.tcp_server_socket.accept()
            # 5. 为这个客户端服务器
            p = multiprocessing.Process(target=self.service_client, args=(client_socket,))
            p.start()
            client_socket.close()

        # 6. 关闭套接字
        self.tcp_server_socket.close()

    def service_client(self, client_socket):
        """为一个客户端服务器"""
        while True:
            recv_data = client_socket.recv(1024)

            # 如果没有数据，那么就意味着对方调用了close
            if not recv_data:
                client_socket.close()
                break

            # 如果对方发送过来了数据，那么就进行相应的处理
            recv_data = recv_data.decode("utf-8", errors="ignore")  # 忽略decode解码失败的字符

            # 测试接收到的数据
            # print(type(recv_data))
            # print(recv_data)
            request_list = recv_data.splitlines()
            print("----->")
            print(request_list)

            try:
                # GET /index.html HTTP/1.1
                request_fires_line = request_list[0]
            except:
                print("请求错误....")
            else:
                ret = re.match(r"[^/]+(/[^ ]+)", request_fires_line)
                if ret:
                    # 提取出 浏览器需要的文件名 例如/xxxx/xxx/x/xx/index.html
                    file_name = ret.group(1)
                else:
                    file_name = "/index.html"


                # 如果不是以.html结尾的请求，那么让web服务器直接服务
                if not file_name.endswith(".html"):
                    print("--接收到的请求信息--file_name=%s------" % file_name)
                    # 合并一个带有路径的文件名
                    file_path_name = STATIC_ROOT + file_name

                    print("--处理之后的请求信息--file_name=%s------" % file_path_name)
                    try:
                        # 打开这个文件
                        f = open(file_path_name, "rb")
                    except:
                        # 如果打不开这个文件，那么也就意味着 404
                        response_body = "访问的页面不存在，请访问正确的网址....."

                        # 组装需要回复的数据 头
                        response_headers = "HTTP/1.1 404 not found\r\n"
                        response_headers += "Content-Type:text/html;charset=utf-8\r\n"
                        response_headers += "Content-Length:%d\r\n" % len(response_body.encode("utf-8"))
                        response_headers += "\r\n"

                        send_data = response_headers + response_body

                        # 返回真正的http应答的数据
                        client_socket.send(send_data.encode("utf-8"))
                    else:
                        # 如果能够打开这个文件，那么也就意味着 200
                        # 从文件中读取数据
                        content = f.read()
                        # 关闭文件
                        f.close()

                        # 组装 body
                        # 返回真正的http应答的数据
                        response_body = content

                        # 组装需要回复的数据 头
                        response_headers = "HTTP/1.1 200 OK\r\n"
                        # response_headers += "Content-Type:text/html;charset=utf-8\r\n"
                        response_headers += "Content-Length:%d\r\n" % len(response_body)
                        response_headers += "\r\n"

                        # 返回真正的http应答的数据
                        client_socket.send(response_headers.encode("utf-8"))
                        client_socket.send(response_body)
                else:
                    # 如果是以.html结尾的请求，那么就传递给web框架进行处理
                    env = dict()
                    env['PATH_INFO'] = file_name
                    response_body = self.app(env, self.set_response_headers)

                    # 组装需要回复的数据 头
                    response_headers = "HTTP/1.1 %s\r\n" % self.response_headers[0]
                    for temp in self.response_headers[1]:
                        # temp=('Content-Type', 'text/html')
                        response_headers += "%s:%s\r\n" % (temp[0], temp[1])
                    response_headers += "Content-Length:%d\r\n" % len(response_body.encode("utf-8"))
                    response_headers += "\r\n"

                    # 返回真正的http应答的数据
                    client_socket.send(response_headers.encode("utf-8"))
                    client_socket.send(response_body.encode("utf-8"))


    def set_response_headers(self, status, headers):
        """保存web框架返回来的header数据"""
        # 找一个属性存储 web框架返回过来的数据
        # ["200 OK",  [('Content-Type', 'text/html')]]
        self.response_headers = [status, headers]

def main():
    """创建一个web服务器，完成整体的控制"""
    if len(sys.argv) == 3:
        # python3 xxxx.py 7890 frame_name:app_name
        port = int(sys.argv[1])
        frame_app_name = sys.argv[2]
    else:
        print("缺少运行的参数，请按照如下格式运行， python3 xxxx.py 7890 frame_name:app_name")
        return

    # mini-frame:app
    ret = re.match(r"([^:]+):(.*)", frame_app_name)
    if ret:
        frame_name = ret.group(1)
        app_name = ret.group(2)
    else:
        print("运行的参数有误，重新运行....")
        return

    sys.path.append("./dynamic")
    frame = __import__(frame_name)
    app = getattr(frame, app_name)

    wsgi_server = WSGIServer(port, app)
    wsgi_server.run_forever()


if __name__ == "__main__":
    main()

