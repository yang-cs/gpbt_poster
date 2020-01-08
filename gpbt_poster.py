from urllib import parse
import requests
import re
import time
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from random import sample,randint
import os, os.path as path


# 素材库大小，即为每个关键字所下载的图片数量，越多选择越大、但下载时间越长。
KW_IMG_COUNT = 20
# 下载图片时的超时设置，默认为 5 秒。
REQ_TIME_OUT = 5
MY_FONTS = ["C:\\WINDOWS\\Fonts\\SIMYOU.TTF","C:\\WINDOWS\\Fonts\\SIMHEI.TTF"]

''' 将关键词拆开后分别搜索相关图片，并以 关键词:图片列表 的形式存入字典并返回 '''
def get_all_image_urls(key_words):
    key_words = key_words.split()
    print(key_words)
    all_urls = {}
    for kw in key_words:
        if kw:
            page_text = requests.get( f'https://image.baidu.com/search/flip?tn=baiduimage&ie=utf-8&word={parse.quote(kw)}&ct=&v=flip').text
             
            all_urls[kw] = re.findall('"objURL":"(.*?)",', page_text, re.S)
            print(f'正在百度 {kw} 主题的素材，请耐心等待')
            time.sleep(2)
    return all_urls

    
''' 从URL字典中取出每个关键词的全部图片URL，分别下载后，以PIL图像对象形式存入二维列表并返回。
    此处根据全局常量 KW_IMG_COUNT 限定了每个关键词的最大图片数量，未成功下载的图片不计在内。
'''
def get_all_images( all_urls ):
    headers={"User-Agent" : "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9.1.6) ",
                "Accept" : "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language" : "en-us",
                "Connection" : "keep-alive",
                "Accept-Charset" : "GB2312,utf-8;q=0.7,*;q=0.7",
                "Referer" : 'https://image.baidu.com/search/flip'}
    img_count = 0
    all_images = []    

    for keyword, url_list in all_urls.items() :
        image_list=[]
        for u in url_list:            
            try:
                response = requests.get(u, headers=headers, timeout=REQ_TIME_OUT)
                image_list.append( Image.open(BytesIO(response.content)) )      

                print(f'正在下载第 {img_count} 张图片素材，相关主题：{keyword}')    
                
                img_count += 1    
                if img_count % KW_IMG_COUNT ==0: 
                    break

            except Exception as e:
                print(f'图片 {u} 下载失败，自动跳过')

        all_images.append(image_list)

    return all_images


''' 从二维图像列表中对每个关键词分别随机抽取若干图像，构成本次拼凑海报的素材。
    然后从结果中随机抽取一张图片，将其复制本作为背景图片。
    最终返回背景图片、以及其他图片（作为前景图）的列表。
'''
def get_samples(all_images):
    fg_images = []

    for images in all_images[0:]:
        i = randint( 1, len(images) )
        fg_images.extend( sample(images,i) )    
    
    bg_image = sample(fg_images,1)[0].copy()

    return bg_image, fg_images


''' 对于传来的一张前景图，将其随机摆放在背景图上。变换过程包括：
    1. 图像尺寸：随机缩放到背景图的 40% 到 70% 之间
    2. 图像角度：随机旋转到原图的 -45 到 45 度之间
    3. 图像位置：随机摆放到背景图范围内
    最终返回粘贴前景图之后的背景图。
'''
def rand_locate( img, bg_image):
    angle = randint(-45,45)
    size_ratio = randint(4,7)/10

    img_width,img_height = img.size
    bg_width,bg_height = bg_image.size

    zoom = size_ratio / max( img_height/bg_height, img_width/bg_width ) 

    temp_img = img.resize( ( int(img_width*zoom), int(img_height*zoom)), Image.ANTIALIAS )
    new_width,new_height = temp_img.size
    
    temp_img = temp_img.convert('RGBA').rotate(angle)

    pos_left = randint( 0, bg_width-new_width)
    pos_up = randint( 0, bg_height - new_height)

    return bg_image.paste(temp_img,(pos_left,pos_up),mask=temp_img.split()[3] )

''' 对于给定的图片（一般为粘贴前景图后），随机添加文字。字体在全局列表 MY_FONTS 中
    随机选择，位置大小与颜色均随机。
    此函数在绘制字体时有时会发生颜色码bytearray index out of range错误，未及调试，
    先用异常处理绕过，后面再改。
'''
def add_words(poster, key_words):
    words = key_words.split()
    bg_width,bg_height = poster.size
    draw = ImageDraw.Draw(poster)

    for _ in range(2,randint(2,8)):
        font = ImageFont.truetype( MY_FONTS[randint(0,len(MY_FONTS))-1], \
             randint( int(bg_width/len(key_words)/2), int(bg_width/len(key_words))))

        try:
            draw.text( (randint(int(bg_width*0.1),int(bg_width*0.7)),  randint(int(bg_height*0.1),int(bg_height*0.7))), \
                    ''.join(sample(words, max(1,randint(0,len(words)-1)))) ,\
                    fill = (randint(0,255),randint(0,255),randint(0,255),randint(0,255)),
                    font = font)
        except Exception as e:            
            draw.text( (randint(int(bg_width*0.1),int(bg_width*0.7)),  randint(int(bg_height*0.1),int(bg_height*0.7))), \
                    ''.join(sample(words, max(1,randint(0,len(words)-1)))) ,  font = font)
    return


''' 指定海报总数，在已经下载好的素材库中随机抽取素材并拼凑海报
'''
def gen_posters(key_words, count, all_images):

    posters = []
    for i in range(count):
        try:
            bg_image,fg_images = get_samples(all_images)
            for fg in fg_images:
                rand_locate(fg, bg_image) 
            
            add_words(bg_image,key_words)
            posters.append(bg_image)
        except Exception as e:
            print(f'因为图片格式等原因，处理第 {i} 张图片时异常，自动跳过：{e}')

    return posters


''' 根据给定的关键字和海报总数，自动生成全部海报并保存到指定文件夹 '''
def main(key_words, count, root_dir):
    try:
        all_images = get_all_images(get_all_image_urls(key_words))
        posters = gen_posters( key_words, count, all_images)

        save_path = f'{root_dir}\\{"".join(key_words.split())}{str(time.time())[-6:]}\\'
        os.mkdir(save_path)
        print(f'现在开始将所有图片导出到 {save_path} 文件夹：')
        for i in range(len(posters)):        
            try:
                posters[i].save( f'{save_path}\\{i}.png')        
            except Exception as e:
                print(f'因为图片格式等原因，保存第 {i} 张图片时异常，自动跳过：{e}')
        print('导出结束，请领导御览。')        

    except Exception as e:
       print('好像有点问题，你自己查吧，本狗歇会。\n', e)



if __name__ == "__main__":
        key_words = input('请输入主题词，用空格分隔：')
        count = int(input('请输入任务数量（整数）：'))
        root_dir = path.split(path.abspath(__file__) )[0]
        
        main(key_words, count, root_dir)


    
