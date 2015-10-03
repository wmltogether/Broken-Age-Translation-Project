# -*- coding: utf-8 -*-
import os,struct,codecs,zlib
from cStringIO import StringIO
import binascii
'''
先读文件尾部，获取子文件个数和文件名索引地址
Now Support Broken Age(Steam , iOS) 
'''
'''
Thanks to https://github.com/bgbennyboy/DoubleFine-Explorer

PCK File Format:
File data with headers
File records
Footer - with file info

Footer at end of file
The last 22 bytes of the file

4 'PACK'
4 0?
2 num files
2 num files again?
4 size of file records section
4 offset of file records section
2 0?

File data for each file

local file header signature 4 bytes ( 0x04034b50 )
version needed to extract 2 bytes
general purpose bit flag 2 bytes
compression method 2 bytes
last mod file time 2 bytes
last mod file date 2 bytes
crc-32 4 bytes
compressed size 4 bytes
uncompressed size 4 bytes
file name length 2 bytes
extra field length 2 bytes
file name ( variable size )
extra field ( variable size )
compressed bytes ( variable size )


File records section

4 0x04030102
2 version needed to extract
2 version needed to extract (again?)
2 general purpose bit flag
2 compression method
2 last mod file time
2 last mod file date
4 CRC32
4 compressed size
4 uncompressed size
4 filename length
10 unknown
4 offset of file data - 1st byte of this dword is xorval for some filenames
x filename
'''
def ParsePCKBundle(f_buffer,F_size):
    NumFiles=0
    offset=0
    PCK_Index_List=[]
    PCK_Filename_List=[]
    f_buffer.seek(offset)    
    while offset<F_size-0x16:
        StandardHeader=0x01020304
        FileRecordsHeader=0x04030102
        Header=struct.unpack('>I',f_buffer.read(4))[0]
        if Header == StandardHeader:
            version=struct.unpack('H',f_buffer.read(2))[0]
            BitFlag=struct.unpack('H',f_buffer.read(2))[0]
            CompressionMethod = struct.unpack('H',f_buffer.read(2))[0]
            FileTime = struct.unpack('H',f_buffer.read(2))[0]
            FileDate = struct.unpack('H',f_buffer.read(2))[0]
            Crc32 = struct.unpack('I',f_buffer.read(4))[0]
            CompressedSize=struct.unpack('I',f_buffer.read(4))[0]
            UncompressedSize=struct.unpack('I',f_buffer.read(4))[0]
            FilenameLength = struct.unpack('H',f_buffer.read(2))[0]
            ExtraFieldLength = struct.unpack('H',f_buffer.read(2))[0]
            Filename=''
            if CompressedSize != UncompressedSize:
                print('Compressed and uncompressed size differ - check compression,offset:%08x'%(offset))
            if CompressionMethod !=0:
                print('Compressed method not 0 !')
            if FilenameLength != 0:
                print('Filename length !=0 !')
                Filename=f_buffer.read(FilenameLength)
            if ExtraFieldLength != 0:
                f_buffer.seek(ExtraFieldLength,1)
            offset=f_buffer.tell()
            f_buffer.seek(CompressedSize,1)
            PCK_Index_List.append((offset,Crc32,\
                                   CompressionMethod,\
                                   CompressedSize,\
                                   UncompressedSize))
            #print('offset:%08x,size:%08x,Filename:%s,CRC32:%08x'%((offset,CompressedSize,Filename,Crc32)))
            NumFiles+=1
            offset=f_buffer.tell()
        else:
            if Header == FileRecordsHeader:
                #print('NumFiles:%d'%NumFiles)
                #Seek back 4 bytes - so we are at the start of the header again
                f_buffer.seek(-4,1)
                #Parse file records
                for k in xrange(NumFiles):
                    #print('tmp NUM:%d'%k)
                    Header = struct.unpack('>I',f_buffer.read(4))[0]
                    if Header != FileRecordsHeader:
                        print('wrong header:%04x,tmp NUM:%d'%(Header,k))
                        #print(len(PCK_Index_List),len(PCK_Filename_List))
                        print('b:Unknown File header %04x, offset:%08x,address:%08x'%(Header,offset,f_buffer.tell()))
                    version=struct.unpack('H',f_buffer.read(2))[0]
                    r_version=struct.unpack('H',f_buffer.read(2))[0]
                    null0=struct.unpack('I',f_buffer.read(4))[0]
                    hash0=struct.unpack('I',f_buffer.read(4))[0]
                    hash1=struct.unpack('I',f_buffer.read(4))[0]
                    CompressedSize=struct.unpack('I',f_buffer.read(4))[0]
                    UnompressedSize=struct.unpack('I',f_buffer.read(4))[0]
                    FilenameLength = struct.unpack('I',f_buffer.read(4))[0]
                    #print('FilenameLength:%04x'%(FilenameLength))
                    null2=struct.unpack('I',f_buffer.read(4))[0]
                    null3=struct.unpack('I',f_buffer.read(4))[0]
                    mark=struct.unpack('H',f_buffer.read(2))[0]
                    FileDataOffset = struct.unpack('I',f_buffer.read(4))[0]
                    XORVal=FileDataOffset & 0xff
                    if XORVal > 0x80:
                        xor0=XORVal
                    else:
                        xor0=0x80 
                    TempStr=f_buffer.read(FilenameLength)
                    Decrypted_Filename=''
                    for j in range(len(TempStr)):
                        Decrypted_Filename+=chr(ord(TempStr[j])^xor0)
                    offset=f_buffer.tell()
                    PCK_Filename_List.append((Decrypted_Filename,version,r_version,\
                                              null0,hash0,hash1,CompressedSize,UnompressedSize,\
                                              null2,null3,mark,FileDataOffset))
            else:
                print('A:Unknown File header %04x, at offset:%08x'%(Header,offset))
    PCK_child_list=[]
    for i in range(len(PCK_Index_List)):
        (offset,Crc32,CompressionMethod,CompressedSize,UncompressedSize)=PCK_Index_List[i]
        (Decrypted_Filename,version,r_version,\
         null0,hash0,hash1,CompressedSize,UnompressedSize,\
         null2,null3,mark,FileDataOffset)=PCK_Filename_List[i]
        PCK_child_list.append((Decrypted_Filename,offset,Crc32,CompressionMethod,\
                               version,r_version,null0,hash0,hash1,\
                               CompressedSize,UncompressedSize,\
                               null2,null3,mark,FileDataOffset))
    return PCK_child_list

def compress_deflate(string):
    compressed_string=zlib.compress(string)[2:-4]
    return compressed_string

def decompress_deflate(string):
    decompressed_string=zlib.decompress(string, -15)
    return decompressed_string

def decompress_tex(tex_texture_buffer):
    tBuffer=StringIO()
    tBuffer.write(tex_texture_buffer)
    tBuffer.seek(0)
    magic=tBuffer.read(4)
    if magic=='\x54\x45\x58\x20':
        width,height=struct.unpack('2H',tBuffer.read(4))
        ver=ord(tBuffer.read(1))
        color_mode=ord(tBuffer.read(1))
        unk=struct.unpack('H',tBuffer.read(2))[0]
        tBuffer.seek(8,1)
        CompressedSize=struct.unpack('I',tBuffer.read(4))[0]
        UncompressedSize=struct.unpack('I',tBuffer.read(4))[0]
        Crc32=struct.unpack('I',tBuffer.read(4))[0]
        zdata=tBuffer.read(CompressedSize)
        dec_data=decompress_deflate(zdata)
    tBuffer.flush()
    if color_mode==0xc:
        #Build PVRTC4 Header For texture
        pBuffer=StringIO()
        pBuffer.write('\x00'*0x34)
        pBuffer.write('\x00'*(width*height/2))
        pBuffer.seek(0)
        pBuffer.write('\x34\x00\x00\x00')
        pBuffer.write(struct.pack('I',width))
        pBuffer.write(struct.pack('I',height))
        pBuffer.seek(4,1)
        pBuffer.write(struct.pack('I',0x8019))
        pBuffer.write(struct.pack('I',(width*height/2)))
        pBuffer.write(struct.pack('I',4))
        pBuffer.seek(0xc,1)
        pBuffer.write(struct.pack('I',1))
        pBuffer.write('PVR!')
        pBuffer.write(struct.pack('I',1))
        pBuffer.write(dec_data)
    if color_mode==0x2:
        #build 32BPP Header For texture
        pBuffer=StringIO()
        pBuffer.write('\x00'*0x34)
        pBuffer.write('\x00'*(width*height*4))
        pBuffer.seek(0)
        pBuffer.write('\x34\x00\x00\x00')
        pBuffer.write(struct.pack('I',width))
        pBuffer.write(struct.pack('I',height))
        pBuffer.seek(4,1)
        pBuffer.write(struct.pack('I',0x8012))
        pBuffer.write(struct.pack('I',(width*height*4)))
        pBuffer.write(struct.pack('I',0x20))
        pBuffer.write(struct.pack('I',0xff))
        pBuffer.write(struct.pack('I',0xff00))
        pBuffer.write(struct.pack('I',0xff0000))
        pBuffer.write(struct.pack('I',0xff000000))
        pBuffer.write('PVR!')
        pBuffer.write(struct.pack('I',1))
        pBuffer.write(dec_data)
    return pBuffer.getvalue()

def getCRC32Value(string):
    #hash string crc32 value
    c_value=binascii.crc32(string)%0x100000000
    return c_value

def getIndexList(package_name):
    index_file=open('%s.txt'%package_name,'rb')
    lines=index_file.readlines()
    index_list=[]
    for i in range(len(lines)):
        if '|' in lines[1]:
            f_list=lines[i].split('|')
            (Filename,offset,Crc32,CompressionMethod)=(f_list[0],int(f_list[1],16),f_list[2],int(f_list[3],16))
            (version,r_version,null0,hash0,hash1)=(int(f_list[4],16),int(f_list[5],16),int(f_list[6],16),int(f_list[7],16),int(f_list[8],16))
            (null2,null3,mark,FileDataOffset)=(int(f_list[9],16),int(f_list[10],16),int(f_list[11],16),\
                                                      int(f_list[12],16))
            index_list.append((Filename,CompressionMethod,version,r_version,null0,hash0,hash1,null2,null3,mark,FileDataOffset))
    return index_list

def RebuildPCKBundle(package_name):
    index_list=getIndexList(package_name)
    num=len(index_list)
    if not os.path.isdir('import\\'): os.makedirs('import\\')
    pack_buffer=open('import//%s'%package_name,'wb')
    name_buffer=StringIO()
    offset=0
    StandardHeader=0x01020304
    FileRecordsHeader=0x04030102 
    for i in range(len(index_list)):
        (Filename,CompressionMethod,version,r_version,null0,hash0,hash1,null2,null3,mark,FileDataOffset)=index_list[i]
        if os.path.exists('patch//%s_unpacked//%s'%(package_name,Filename)):
            print('using patch file:%s'%Filename)
            ResourcesFile=open('patch//%s_unpacked//%s'%(package_name,Filename),'rb')
        else:
            ResourcesFile=open('%s_unpacked//%s'%(package_name,Filename),'rb')
        ResourcesData=ResourcesFile.read()
        ResourcesFile.close()
        Crc32=getCRC32Value(ResourcesData)
        CompressedSize=len(ResourcesData)
        UncompressedSize=CompressedSize
        version=0x14
        BitFlag=0
        FileTime=0x839c
        FileDate=0x436e
        if CompressionMethod==0:
            UncompressedSize=CompressedSize
        FileDataOffset=pack_buffer.tell()    
        pack_buffer.write(struct.pack('>I',StandardHeader))
        pack_buffer.write(struct.pack('H',version))
        pack_buffer.write(struct.pack('H',BitFlag))
        pack_buffer.write(struct.pack('H',CompressionMethod))
        pack_buffer.write(struct.pack('H',FileTime))
        pack_buffer.write(struct.pack('H',FileDate))
        pack_buffer.write(struct.pack('I',Crc32))
        pack_buffer.write(struct.pack('I',CompressedSize))
        pack_buffer.write(struct.pack('I',UncompressedSize))
        pack_buffer.write(struct.pack('H',0))
        pack_buffer.write(struct.pack('H',0))
        pack_buffer.write(ResourcesData)
        #then build name block
        name_buffer.write(struct.pack('>I',FileRecordsHeader))
        name_buffer.write(struct.pack('H',version))
        name_buffer.write(struct.pack('H',r_version))
        name_buffer.write(struct.pack('I',null0))
        name_buffer.write(struct.pack('I',hash0))
        name_buffer.write(struct.pack('I',hash1))
        name_buffer.write(struct.pack('I',CompressedSize))
        name_buffer.write(struct.pack('I',UncompressedSize))
        name_buffer.write(struct.pack('I',len(Filename)))
        name_buffer.write(struct.pack('I',null2))
        name_buffer.write(struct.pack('I',null3))
        name_buffer.write(struct.pack('H',mark))
        name_buffer.write(struct.pack('I',FileDataOffset))
        XORVal=FileDataOffset&0xff
        if XORVal<0x80:
            XORVal=0x80
        Encrypted_Filename=''
        for j in range(len(Filename)):
            Encrypted_Filename+=chr(ord(Filename[j])^XORVal)
        name_buffer.write(Encrypted_Filename)
    name_start_addr=pack_buffer.tell()
    nameblock=name_buffer.getvalue()
    pack_buffer.write(nameblock)
    name_buffer.flush()
    pack_buffer.write('PACK')
    pack_buffer.write('\x00'*4)
    pack_buffer.write(struct.pack('H',num))
    pack_buffer.write(struct.pack('H',num))
    pack_buffer.write(struct.pack('I',len(nameblock)))
    pack_buffer.write(struct.pack('I',name_start_addr))
    pack_buffer.write('\x00\x00')
    pack_buffer.close()

def extract_pck(fn):
    f=open(fn,'rb')
    F_size=os.path.getsize(fn)
    PCK_child_list=ParsePCKBundle(f,F_size)
    print('%s---->decompressing.....!'%fn)
    log=open('%s.txt'%fn,'wb')
    for i in range(len(PCK_child_list)):
        (Filename,offset,Crc32,CompressionMethod,\
         version,r_version,null0,hash0,hash1,\
         CompressedSize,UncompressedSize,\
         null2,null3,mark,FileDataOffset)=PCK_child_list[i]
        log.write('%s|%08x|%04x|%x|'%(Filename,offset,Crc32,CompressionMethod)+\
              '%04x|%04x|%04x|%04x|%04x|'%(version,r_version,null0,hash0,hash1)+\
              '%04x|%04x|%04x|%08x|\r\n'%(null2,null3,mark,FileDataOffset))
        fldr='/'.join(Filename.split(r'/')[:-1])
        name=Filename.split(r'/')[-1]
        if not os.path.isdir('%s_unpacked\\%s\\'%(fn,fldr)): os.makedirs('%s_unpacked\\%s\\'%(fn,fldr))
        dest=open('%s_unpacked\\%s'%(fn,Filename),'wb')
        f.seek(offset)
        data=f.read(CompressedSize)
        dest.write(data)
        dest.close()
    print('%s---->OK!'%fn)
    log.close()
    f.close()


