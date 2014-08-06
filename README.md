SmashTheAddress
===============

SmashTheAddress是一个python脚本，它利用Atosl把一个官方格式的ios crashlog解析成可读的log。可以实现在Linux解析crashlog。

Atosl一个命令行工具，是Atos的一个开源实现（atos可以利用dsym文件，把address转换成Symbol）。

##Install

虽然python脚本可以跨平台，但需要编译安装atosl。

- 安装编译atosl的依赖：
	- libdwarf：
		- mac:`brew install libdwarf`
		- ubuntu:`sudo apt-get install libdwarf-dev`
		- centos: 如果yum中没有，可以到sourceforg中下载源代码 `./configure` `make install`
	- libiberty:
		- mac: `brew install binutils` ，并在atosl代码目录下的config.mk 中的`LDFLAGS`加入 `-L/usr/local/Cellar/binutils/2.24/lib/x86_64/`
		- ubuntu: `sudo apt-get install libiberty-dev` 或者自己下deb包（ubuntu13下需要自己下），` sudo dpkg -i ***.deb`
		- centos: unknow
	
- 编译atosl。进入代码目录下的atosl-d文件夹，`sudo make install`
- 如果是linux，需要复制iOS动态链接库。动态链接库的在mac下的目录为`~/Library/Developer/Xcode/iOS DeviceSupport/`(需要所有需要解析的版本库，该目录下有大部分，但是不全)。比如复制到当前目录 `./syslib`
- python脚本需要python 2.7，请安装正确版本。

##Use
1 `python SmashTheAddress.py path/to/dsym  path/to/crashlog`   or

2 `python SmashTheAddress.py -d path/to/dsym -l path/to/Lib/root  -f path/to/crashlog`

    -f         : path to crashlog file
    -d         : path to dSYM file (not the bundle of .dsym file, but the binary in that
    -l         : set the root path of iOS's system dynamic link libs. 
    -h, --help : Print this.
    
代码包中有Demo数据：

`python SmashTheAddress.py -d demodata/MyPaper.app.dSYM/Contents/Resources/DWARF/MyPaper -f demodata/crash -l ./syslib`
