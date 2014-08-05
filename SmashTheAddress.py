import os
import subprocess
import re
import sys
#------------------- macro ------------------

useCustomVersionAtosl = True

staticStringDefaultPathToLibPrefix = os.path.expanduser("~") + "/Library/Developer/Xcode/iOS DeviceSupport/"


#------------------- symbolicating ---------------------

def symbolicateAddress(binaryPath, archtechture, loadAddress, lookUpAddrList):
    """ function to symbolicate address
    """
    #command = "atosl -o %s -A %s -l %s" % (binaryPath, archtechture, loadAddress)
    command = ["atosl",'-o', binaryPath, '-A', archtechture, '-l', loadAddress]
    command.extend( lookUpAddrList )
    output = ""
    
    try:
        output = subprocess.check_output(command , shell = False)
    # http://cleverdeng.iteye.com/blog/888986
    # Acoording to this blog, it expend 25% more time
    except:
        print """[Error] when call atosl to symbolicate address. may be problems below :
            atosl is not installed;
            binary is not exsit;
            arch is not contained in the binary;\n""" + " ".join(command)
    return output

def symbolicateAddressCustomed(binaryPath, archtechture, loadAddress, lookUpAddrList, isDsym):
    """ function to symbolicate address
        """
    #command = "atosl -o %s -A %s -l %s" % (binaryPath, archtechture, loadAddress)
    command= []
    if isDsym:
        command = ["atosl",'-o', binaryPath, '-A', archtechture,'-d', '-l', loadAddress]
    else:
        command = ["atosl",'-o', binaryPath, '-A', archtechture, '-l', loadAddress]
    
    command.extend( lookUpAddrList )
    output = ""

    try:
        output = subprocess.check_output(command , shell = False)
        # http://cleverdeng.iteye.com/blog/888986
        # Acoording to this blog, it expend 25% more time
    except:
        print """[Error] when call atosl to symbolicate address. may be problems below :
                     atosl is not installed;
                     binary is not exsit;
                     arch is not contained in the binary;\n""" + " ".join(command)
    return output          

#------------------- classes ---------------------

class ThreadLine(object):
    """ Class represent a line in the backtrace. like: 
        `5  libobjc.A.dylib  0x3839af68 0x38397000 + 16232 `
    """
    def __init__(self, text):
        self.text = text;
        self.symbolicatedText = ''
        self.lineNumber = ''
        self.threadName = ''
        self.address = ''
        self.loadAddress = ''
        parts = self.text.split()  
        # ['0', 'libsystem_kernel.dylib', '0x3894f1f0', '0x3893c000', '+', '78320']

        if len( parts ) == 6:
            self.lineNumber = parts[0]
            self.threadName = parts[1]
            self.address = parts[2]
            self.loadAddress = parts[3]
            self.offset = parts[5]
        else:
            print '[Error] when read thread line\n' + self.text
        pass

class ExceptionBacktraceLine(ThreadLine):

        def __init__(self, address):
            # super variable
            self.symbolicatedText = ''
            self.threadName = ''
            self.address = ''
            self.loadAddress = ''

            # new variable
            self.address = address
            self.image = None



class Image(object):
    """ Class represent a binary image that contain load info
    """
    def __init__(self, text, pathToSysLibRoot):
        self.loadAddress = 0
        self.loadAddressString = ''
        self.loadAddress_end = 0
        self.name = ''
        self.archtecture = ''
        #self.uuid = ''
        self.path = ''

        # init varables
        parts = text.split()  
        # ['0x76000', '-', '0x76fff', 'MobileSubstrate.dylib', 'armv6', '<ad3e6cb9e915360ebc71ccbf27bc4ea7>', '/Library/MobileSubstrate/MobileSubstrate.dylib']
        if len(parts) == 7:
            self.loadAddress = long( parts[0], 0 )
            self.loadAddress_end = long( parts[2], 0 )
            self.loadAddressString = parts[0]
            self.name = parts[3]
            self.archtecture = parts[4]
            #self.uuid = parts[5].strip("<>")
            self.path = pathToSysLibRoot + parts[6]
        else:
            print '[Error] when read image line\n' + text
        pass

    def __hash__(self):
        return hash((self.name, self.loadAddress))

    def __eq__(self, other):
        return (self.name, self.loadAddress) == (other.name, other.loadAddress)

    # def symbolicateThreadLine(self, listOfThreadLine):
    #     addressList = [threadLine.address for threadLine in listOfThreadLine]
    #     output = symbolicateAddress(self.path, self.archtecture, self.loadAddressString, addressList)
    # 
    #     # save the formatted text in thread line object itself
    #     outputList = output.splitlines()
    #     if len(outputList) != len(addressList):
    #         print "[Error] non-correct output of atos of image %s" % self.name
    #     else:
    #         i = 0
    #         for threadLine in listOfThreadLine:
    #             threadLine.symbolicatedText = outputList[i]
    #             i += 1
    #     pass
     
    def symbolicateThreadLine(self, listOfThreadLine):
        
        # only use atosl symbolicate unique address
        uniqueList = list( set([threadLine.address for threadLine in listOfThreadLine]) )
        output = symbolicateAddress(self.path, self.archtecture, self.loadAddressString, uniqueList)
        outputList = output.splitlines()

        if len(outputList) != len(uniqueList):
            print "[Error] non-correct output of atos of image %s" % self.name
            
        # save the result to a dict, then get the final result from this dict
        # resultDict, key is address, value is formatted text
        resultDict = {}

        for i in xrange(len(uniqueList)):
            address = uniqueList[i]
            formatedText = outputList[i]
            resultDict[address] =  formatedText
        
        for threadLine in listOfThreadLine:
            threadLine.symbolicatedText = resultDict[threadLine.address]
        pass
            
    

class OurAppImage(Image):     

    def __init__(self, text, pathToDsym):
        super(OurAppImage,self).__init__(text,"whatever")
        self.path = pathToDsym
        pass
    
    def symbolicateThreadLine(self, listOfThreadLine):
        uniqueList = list( set([threadLine.address for threadLine in listOfThreadLine]) )
        output = symbolicateAddressCustomed(self.path, self.archtecture, self.loadAddressString, uniqueList, useCustomVersionAtosl)
        outputList = output.splitlines()
        
        if len(outputList) != len(uniqueList):
            print "[Error] non-correct output of atos of image %s" % self.name
            
        resultDict = {}
        
        for i in xrange(len(uniqueList)):
            address = uniqueList[i]
            formatedText = outputList[i]
            resultDict[address] =  formatedText
        
        for threadLine in listOfThreadLine:
            threadLine.symbolicatedText = resultDict[threadLine.address]
        pass


""" Section Class
"""            

class CrashTextSection(object):

    def __init__(self, text):
        self.text = text.strip()
        self.iterOfLine = None
        self.lines = None

    def iterationOfLines(self):
        if self.iterOfLine is None:
            self.iterOfLine = self.text.splitlines()
        return self.iterOfLine

    def allLines(self):
        if self.lines is None:
            self.lines = list( self.iterationOfLines())
        return self.lines

    def getSectionHeaderText(self):
        # override this method if in specific situation 
        for line in self.iterationOfLines():
            return line # return the first line.

class HeaderInfoSection(CrashTextSection):

    def __init__(self, text):
        super(HeaderInfoSection,self).__init__(text)
        self.systemVersion = ""
        self._initSystemVerison()

    def _initSystemVerison(self):
        pattern = r'\d[.\d]+ \(\w+\)'
        results = re.findall(pattern, self.text)
        if len(results) == 0:
            print "[Error] cannot find the right OS verison"
            raise AssertionError()
        else:
            # the line below sucks !
            self.systemVersion = results[0]
#             self.systemVersion = self.systemVersion.replace(" ",'\ ')
#             self.systemVersion = self.systemVersion.replace('(', '\(')
#             self.systemVersion = self.systemVersion.replace(')', '\)')


class ExceptionBacktraceSection(CrashTextSection):

    def __init__(self, text):
        super(ExceptionBacktraceSection, self).__init__(text)
        self._allThreadLineObject = None
        self._headerText = ""

    def _getAllBacktraceAddress(self):
        allLines = self.allLines()
        backtraceString = ""
        if len(allLines) >= 1:
            self._headerText = allLines[0]
            backtraceString = allLines[1]
            backtraceString = backtraceString.strip("( )")
        backtraceList = backtraceString.split(" ")
        return backtraceList

    def allThreadLineObject(self):
        if self._allThreadLineObject is None:
            objects = []
            for address in self._getAllBacktraceAddress():
                objects.append(ExceptionBacktraceLine(address))
            self._allThreadLineObject = objects

        return self._allThreadLineObject

    def findAllLoadAddress(self, imageAddressSection):
        for exceptionAddressObject in self.allThreadLineObject():
            image = imageAddressSection.searchImageWithAddressUsingCache(exceptionAddressObject.address)
            if image is None:
                print "[Error] cannot find image for exception backtrace address:" + exceptionAddressObject.address
            else:
                exceptionAddressObject.image = image
                exceptionAddressObject.loadAddress = image.loadAddressString
                exceptionAddressObject.threadName = image.name
        pass

    def getSymbolicatedText(self): 
        assert ( self._allThreadLineObject ) 
        textList = []
        textList.append( self._headerText )

        i = 0
        for exceptionAddrLine in self._allThreadLineObject:
            newline = "%-4d%-31s %s %s" % (i, exceptionAddrLine.threadName, exceptionAddrLine.address, exceptionAddrLine.symbolicatedText)
            textList.append( newline )
            i += 1

        return "\n".join(textList)

class ThreadBacktraceSection(CrashTextSection):

    def __init__(self, text):
        super(ThreadBacktraceSection, self).__init__(text)

        self._allThreadLineObject = None
        self._headerLinesNum = self._getHeaderLineNum()

    def _getHeaderLineNum(self): 
        num = 0
        for line in self.iterationOfLines()[:2]:
            if line[:6] == 'Thread':
                num += 1
        return num

    def getSectionHeaderText(self):
        headerText = '\n'.join(list(self.iterationOfLines()[ :self._headerLinesNum]))
        return headerText

    def _generatorOfThreadLineObjects(self):
        for line in self.iterationOfLines()[self._headerLinesNum: ]:
            yield ThreadLine(line)

    def allTreadLineObjects(self):
        if self._allThreadLineObject is None:
            self._allThreadLineObject = list( self._generatorOfThreadLineObjects() )
        return self._allThreadLineObject

    def getSymbolicatedText(self): 
        assert ( self._allThreadLineObject ) # must call allTreadLineObjects to init the thread object ,then symbolicate it seprately 
        textList = []
        textList.append( self.getSectionHeaderText() )

        for threadLine in self._allThreadLineObject:
            newline = "%-4s%-31s %s %s" % (threadLine.lineNumber, threadLine.threadName, threadLine.address, threadLine.symbolicatedText)
            textList.append( newline )

        return "\n".join(textList)


class BinaryAddressSection(CrashTextSection):

    def __init__(self,text,pathToDsym,pathToSysLibRoot):
        super(BinaryAddressSection, self).__init__(text)

        self.imageObjects = []
        self._cacheDict ={}
        # init varibles
        appImage = OurAppImage(self.iterationOfLines()[1], pathToDsym)
        self.imageObjects.append(appImage)

        for line in self.iterationOfLines()[2:]:
            libImage = Image(line, pathToSysLibRoot)
            self.imageObjects.append(libImage)

    def searchImageWithAddress(self, addressNum):
        # address is a number
        # return a Image object
        # half-search. the image objects is already sorted, so it's simple
        if type(addressNum) is str:
            addressNum = long(addressNum,0)

        #TODO use dict 
        def searchImageWithAddressInner(headIndex, tailIndex):
            index = headIndex + int((tailIndex - headIndex) / 2)
            returnImage = self.imageObjects[index]

            if returnImage.loadAddress <= addressNum and addressNum <= returnImage.loadAddress_end :
                return returnImage
            elif headIndex == tailIndex:
                return returnImage  # the end of search, whether or not it find the right image
            elif addressNum > returnImage.loadAddress:
                return searchImageWithAddressInner(index+1, tailIndex)
            else:
                return searchImageWithAddressInner(headIndex, index)

        returnImage = searchImageWithAddressInner(0, len(self.imageObjects)-1)
        return returnImage

    def searchImageWithAddressUsingCache(self, address):
        image= None
        if not address in self._cacheDict:
            image = self.searchImageWithAddress(address)
            self._cacheDict[address] = image
        else:
            image = self._cacheDict[address]
        return image

class CrashFile(object):

    def __init__(self, crashPath, dsymPath, systemLibRootPath):
        self.crashPath = crashPath
        self.dsymPath = dsymPath
        self.systemLibRootPath = ""

        self.headerSection = None
        self.exceptionSection = None
        self.threadSectionList = []  # ThreadLine objects
        self.registerSection = ""
        self.imagesSection = None

        # init

        with open(crashPath) as f:
            pattern = r"((Thread [0-9]+ name:.*\n)?((Thread [0-9]+( Crashed)*):\n))|(Last Exception Backtrace:\n)|(Thread [0-9]+ crashed with)|(No thread state)|(Binary Images:)"
            text = f.read()
            iterator = re.finditer(pattern, text)
            textParts = []
            lastIndex = 0

            for match in iterator:
                index = match.start(0)  # the default group argument is 0
                textParts.append( text[lastIndex:index] )
                lastIndex = index

            textParts.append(text[lastIndex:])

            if len(textParts) < 4:
                print "[Error] It's not a valid formatted crash log file"
                raise AssertionError()
            else:
                
                # header section
                self.headerSection = HeaderInfoSection(textParts[0].strip())
                self.systemLibRootPath = systemLibRootPath.rstrip("/") + "/"+self.headerSection.systemVersion + "/Symbols"  # init path for lib
                if not os.path.isdir(self.systemLibRootPath):
                    print "[Warning] path to system dynamic lib is invalid.\n" + self.systemLibRootPath
                    
                # exception section
                threadStartIndex = 1
                if textParts[1][:4] == "Last":
                    self.exceptionSection = ExceptionBacktraceSection( textParts[1].strip() )
                    threadStartIndex = 2

                # thread section
                for t in textParts[threadStartIndex : -2]:
                    aThreadSection = ThreadBacktraceSection(t.strip())
                    self.threadSectionList.append(aThreadSection)
                
                # image section
                self.imagesSection = BinaryAddressSection( textParts[-1].strip(), self.dsymPath, self.systemLibRootPath)
                
                # registerSection
                registerText = textParts[-2].strip()
                if "r0" in registerText or "No thread" in registerText:
                    self.registerSection = registerText
                else:
                    self.registerSection = ""
                
                # prepare the exception section
                self.exceptionSection.findAllLoadAddress(self.imagesSection)



    def smashTheAddresses(self):
        # firsly init the Path to lib root, in order to symbolicate the dynamic link lib

        # atosl tool can pass servel addr in one command. It's
        # faster than symbolicate one addr in one command. So we
        # put all address of same binary image together, then sym-
        # bolicate them together.
        # 
        # a dict :
        #         key   is a image('s load address),
        #         value is a list of its threadlines  
        dictionry = {}

        # move get all image used in thread backtrace
        for threadSection in self.threadSectionList:
            allObjects = list(threadSection.allTreadLineObjects())  # make a new list
            allObjects.extend(self.exceptionSection.allThreadLineObject())
            for threadLine in allObjects:
                # get its image
                image = self.imagesSection.searchImageWithAddressUsingCache(threadLine.loadAddress)   
                if image not in dictionry:
                    dictionry[image] = [threadLine]
                else:
                    addrList = dictionry[image]
                    addrList.append(threadLine)

        # smash the address
        for image in dictionry:
            image.symbolicateThreadLine(dictionry[image])
            # the output save in threadline object
        pass

    def generateFormattedCrashLogText(self):
        textList = []
        textList.append(self.headerSection.text)
        textList.append(self.exceptionSection.getSymbolicatedText())
        for section in self.threadSectionList:
            textList.append(section.getSymbolicatedText())

        textList.append(self.registerSection)
#         textList.append(self.imagesSection.text)

        symbolicatedCrashLog = '\n\n'.join(textList)
        return symbolicatedCrashLog 

#-------------------- main function ---------------------------



def SmashTheAddressesMain(crashPath,dsymPath,systemLibRootPath):       
    crashObject = CrashFile(crashPath,dsymPath,systemLibRootPath)
    crashObject.smashTheAddresses()
    return crashObject.generateFormattedCrashLogText()


def getPathsFromCommandArguments():

    crashPath = ''
    dsymPath = ''
    systemLibRootPath = staticStringDefaultPathToLibPrefix

    helpInfoStart = "    SmashTheAddress. A tool to symbolicate iOS's crash log using `atosl`. Arguments should in format like:"
    helpInfoString = """

        1 `SmashTheAddress path/to/dsym  path/to/crashlog`   or
        2 `SmashTheAddress -d path/to/dsym -l path/to/Lib/root  -f path/to/crashlog`

    requird:
        -f         : path to crashlog file
        -d         : path to dSYM file (not the bundle of .dsym file, but the binary in that

    optional:
        -h, --help : Print this.
        -l         : set the root path of iOS's system dynamic link libs. Default value is `~/Library/Developer/Xcode/iOS DeviceSupport/`
"""

    numOfArgv = len(sys.argv)
    argFormatSimpleMode = True
    for v in sys.argv:
        if v[:1] == "-":
            argFormatSimpleMode = False
            break

    try:
        if argFormatSimpleMode:
            # should in format like this
            # `SmashTheAddress path/to/dsym  path/to/crashlog`

            crashPath,dsymPath = sys.argv[2],sys.argv[1]

        else:
            # should in format like this
            # `SmashTheAddress -d path/to/dsym -l path/to/Lib/root  -f path/to/crashlog`

            # check the format

            i = 0
            for v in sys.argv[1:]:
                if i % 2 == 0:
                    assert( v[:1] == "-")
                else:
                    assert( v[:1] != "-")
                i += 1

            # -h help info
            if "-h" in sys.argv[1:] or "--help" in sys.argv[1:]:
                print helpInfoStart + helpInfoString
                return 

            # 
            if numOfArgv != 7:
                raise AssertionError()

            # if the format is valid, put it in a dict
            argvDict = {}
            for i in xrange(1,numOfArgv,2):
                argvDict[sys.argv[i]] = sys.argv[i+1]


            crashPath = argvDict["-f"]
            dsymPath = argvDict["-d"]
            if "-l" in argvDict:
                systemLibRootPath = argvDict["-l"]
    except:
        print "\n    [Invalid Arguments]  Arguments should in format like:" + helpInfoString
        return

    return (crashPath,dsymPath,systemLibRootPath)        


if __name__ == "__main__":

    paths = getPathsFromCommandArguments()
    if paths is None:
        pass
    else:
        (crashPath,dsymPath,systemLibRootPath) = paths
        print SmashTheAddressesMain(crashPath,dsymPath,systemLibRootPath)
    
#    crashPath = os.path.expanduser("~") +"/wor/symbolication/atos/a app/crash"
#    dsymPath = os.path.expanduser("~") +'/wor/symbolication/atos/a app/MyPaper.app.dSYM/Contents/Resources/DWARF/MyPaper'
#    systemLibRootPath = staticStringDefaultPathToLibPrefix
#    print SmashTheAddressesMain(crashPath,dsymPath,systemLibRootPath)


