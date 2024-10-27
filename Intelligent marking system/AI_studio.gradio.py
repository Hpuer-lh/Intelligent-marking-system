from paddleocr import PaddleOCR
import zipfile
import os
import glob
import gradio as gr
import erniebot
import cv2
import numpy as np
import shutil
import copy
import time
import random

erniebot.api_type = 'aistudio'
erniebot.access_token = "f6605a9c8c8edf921b29af1180a4b3dd23dbcb3d"
destination_path = './test'
demo_path = './do'

if not os.path.exists('test'):
    os.mkdir('test')

model = "ernie-3.5"
amessages = [{'role': 'user',
             'content': "你现在的任务是评阅考生试卷,我将先后分别输入考生的试卷答案与标准答案。"}]
first_response = erniebot.ChatCompletion.create(
    model=model,
    messages=amessages,
)
amessages.append({'role': 'assistant', 'content': first_response.result})

ocr = PaddleOCR(det_model_dir='./output/',
                rec_model_dir='./inf/',
                det_max_side_len=2000,
                det_db_box_thresh=0.5,
                det_db_unclip_ratio=2.0,
                drop_score=0,
                max_text_length=40,
                # det_db_thresh=0.5,
                # det_db_score_mode="slow",
                det_algorithm="DB",
                # show_log=True,
                use_angle_cls=True)


def process_files(fort, picture, text):
    # 模型路径下必须含有model和params文件
    global model, amessages
    messages = copy.deepcopy(amessages)
    result = ocr.ocr(picture, cls=True)
    ocr_result1 = ""
    for idx in range(len(result)):
        res = result[idx]
        for line in res:
            ocr_result1 = ocr_result1 + " " + str(line[1][0])
    messages.append({'role': 'user',
                     'content': "首先，本题的试卷科目为：\n{}\n由于考生的试卷答案从OCR文字识别的结果中获取,你需要结合上下文语义以及评阅科目性质进行综合判断，矫正识别后的考生答案。以下文字是考生的试卷答案：\n{}\n请给出你根据语境、语义以及考试科目给出矫正后的考生试卷答案".format(fort,ocr_result1)+ "然后，你需要根据上文矫正后的考生答案以及给出的参考答案，对考生的作答情况进行解法点评以及给予对考生的后续学习建议并结合上下文语义进行综合判断考生答案以便基于合理化结果。你的回答模板为‘通过分析对比发现，该考生的试卷解法点评与后续学习建议如下：...’。以下文字是试卷的参考答案，{}".format(text)})

    second_response = erniebot.ChatCompletion.create(
        model=model,
        messages=messages,
    )
    messages.append({'role': 'assistant', 'content': second_response.result})

    messages.append({'role': 'user',
                     'content': "针对该考生试卷的答案和解法点评，参考上文参考答案,对学生作答情况给予'A'，'B','C','D','E'五个等级评价结果，要求等级合理化，只需回答等级对应的字母即可，不必给出分析过程。你的回答模板为‘A’或‘B’或‘C’或‘D’或‘E’。"})
    eventual_response = erniebot.ChatCompletion.create(
        model=model,
        messages=messages,
    )

    return second_response.result, str(eventual_response.result)


def submit_input(fort, image, anwser):
    try:
        global model, amessages
        messages = copy.deepcopy(amessages)
        if image is None:
            data = 0
        elif isinstance(image, np.ndarray):
            data = 1
        if len(fort) == 0 or data == 0 or len(anwser) == 0:
            with open('帮助文档.txt', 'w') as f:
                f.write("若问题还未解决，请查看您要批阅的答题卡照片、标准答案以及评阅科目是否正确输入！\n                            ——由背水一战团队撰写")
            advice, score,file,flag = "评阅失败，请查看您要批阅的答题卡照片、标准答案以及评阅科目是否正确输入！", "Error", '帮助文档.txt',1
        else:
            flag = 0
        for i in range(3):
            if i == 0 and flag ==0 :
                result = ocr.ocr(image, cls=True)
                ocr_result1 = ""
                for idx in range(len(result)):
                    res = result[idx]
                    for line in res:
                        ocr_result1 = ocr_result1 + " " + str(line[1][0])
                advice, score,file = "正在认真评阅中，请您耐心等待...", None,None
            if i == 1 and flag ==0 :
                messages.append({'role': 'user',
                                 'content': "首先，本题的试卷科目为：\n{}\n由于考生的试卷答案从OCR文字识别的结果中获取,你需要结合上下文语义以及评阅科目性质进行综合判断，矫正识别后的考生答案。以下文字是考生的试卷答案：\n{}\n请给出你根据语境、语义以及考试科目给出矫正后的考生试卷答案".format(fort, ocr_result1) + "然后，你需要根据上文矫正后的考生答案以及给出的参考答案，对考生的作答情况进行解法点评以及给予对考生的后续学习建议并结合上下文语义进行综合判断考生答案以便基于合理化结果。你的回答模板为‘通过分析对比发现，该考生的试卷解法点评与后续学习建议如下：...’。以下文字是试卷的参考答案，{}".format(anwser)})
                second_response = erniebot.ChatCompletion.create(
                    model=model,
                    messages=messages,
                )
                messages.append({'role': 'assistant', 'content': second_response.result})
                advice, score = second_response.result, "?"
                advice = "当前评阅科目为：{}\n".format(fort) + advice
                with open('result.txt', 'w') as f:
                    f.write("该同学的评卷建议以及建议得分如下：" + '\n')
                    f.write(advice + '\n')
                    f.write(score)
                file = 'result.txt'
            elif i == 2 and flag ==0:
                messages.append({'role': 'user',
                                 'content': "针对该考生试卷的答案和解法点评，参考上文参考答案,对学生作答情况给予'A'，'B','C','D','E'五个等级评价结果，要求等级合理化，只需回答等级对应的字母即可，不必给出分析过程。你的回答模板为‘A’或‘B’或‘C’或‘D’或‘E’。"})
                eventual_response = erniebot.ChatCompletion.create(
                    model=model,
                    messages=messages,
                )
                score = str(eventual_response.result)
                with open('result.txt', 'w') as f:
                    f.write("该同学的评卷建议以及建议得分如下：" + '\n')
                    f.write(advice + '\n')
                    f.write(score)
                file='result.txt'
            yield advice, score, file
    except Exception:
        with open('帮助文档.txt', 'w') as f:
            f.write(
                "若问题还未解决，请查看您要批阅的答题卡照片以及标准答案是否输入！\n                            ——由背水一战团队撰写")
            advice, score = "评阅失败，请查看您要批阅的答题卡照片以及标准答案是否输入！", "？"
        return advice, score, '帮助文档.txt'


def demo_do():
    data_file = glob.glob(os.path.join(demo_path, '*.jpg'))
    image_data = random.choice(data_file)
    with open(image_data, 'rb') as f:
        image = f.read()
    np_arr = np.frombuffer(image, np.uint8)
    image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    anwser = "【答案】(1)异：美国：美国铁路起步早、发展速度快；美国铁路发展主要受工业革命的影响；美国铁路运输取代了运河运输；二战后美国铁路运输地位逐渐下降；美国铁路以货运为主；（每点2分，写出2点即可）\n中国：中国近代铁路起步晚、发展速度慢，新中国成立后发展速度较快；中国铁路发展受政局变化影响；中国铁路运输取代了人力、畜力运输；新中国成立后中国铁路运输地位稳步上升；中国铁路客、货并重。（每点2分，写出2点即可）\n (2)意义：美国：维护了联邦政府的统一；降低了运输成本，促进了经济发展；有利于西部开发；加快了美国工业化进程和社会转型。（每点2分，写出3点即可）\n中国：近代时期：改变了人们的出行方式，有助于中国近代化发展。新中国成立后：加强区域经济联系，有利于地区经济均衡发展；促进各民族共同繁荣；改善人们的生活质量；带动了城市格局、人口布局和经济版图的积极变化，促进了国家现代化进程。（每点2分，写出3点即可）\n(3)原因：坚持党的领导；充分发挥社会主义制度的优势；坚持人民铁路为人民的宗旨；深化改革建立适应市场经济的机制；坚持自立自强，持续推动科技创新。（每点2分，写出3点即可）"
    format = "历史"
    return format, image, anwser


def demos_do():
    print(1111111111111111)
    data_file = glob.glob(os.path.join(demo_path, '*.jpg'))
    anwser = "【答案】(1)异：美国：美国铁路起步早、发展速度快；美国铁路发展主要受工业革命的影响；美国铁路运输取代了运河运输；二战后美国铁路运输地位逐渐下降；美国铁路以货运为主；（每点2分，写出2点即可）\n中国：中国近代铁路起步晚、发展速度慢，新中国成立后发展速度较快；中国铁路发展受政局变化影响；中国铁路运输取代了人力、畜力运输；新中国成立后中国铁路运输地位稳步上升；中国铁路客、货并重。（每点2分，写出2点即可）\n (2)意义：美国：维护了联邦政府的统一；降低了运输成本，促进了经济发展；有利于西部开发；加快了美国工业化进程和社会转型。（每点2分，写出3点即可）\n中国：近代时期：改变了人们的出行方式，有助于中国近代化发展。新中国成立后：加强区域经济联系，有利于地区经济均衡发展；促进各民族共同繁荣；改善人们的生活质量；带动了城市格局、人口布局和经济版图的积极变化，促进了国家现代化进程。（每点2分，写出3点即可）\n(3)原因：坚持党的领导；充分发挥社会主义制度的优势；坚持人民铁路为人民的宗旨；深化改革建立适应市场经济的机制；坚持自立自强，持续推动科技创新。（每点2分，写出3点即可）"
    format = "历史"
    data_format = '.jpg'
    result_format = '逐一输出'
    print(22222222222222222222222222)
    return format, data_file, anwser, data_format, result_format


def clear_input():
    image = None
    format = []
    anwser = ''
    return image, format, anwser


def clears_input():
    data_file = None
    format = []
    anwser = ''
    data_format = []
    result_format = []
    return data_file, format, anwser, data_format, result_format


def stop_do():
    global flag
    if flag == 1:
        flag = 0


def clear_folder(folder_path):
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path) or os.path.islink(file_path):
            os.unlink(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)


def rename_files(directory, data_format):
    i = 1
    for filename in os.listdir(directory):
        if os.path.isfile(os.path.join(directory, filename)):
            new_name = "学生答案 ({})".format(i) + data_format
            os.rename(os.path.join(directory, filename), os.path.join(directory, new_name))
            i += 1

def process_file(fort, input_files, text, data_format, result_format):
    try:
        global destination_path, flag
        clear_folder(destination_path)
        i = 1
        flag = 1
        file_list=[]
        if input_files is None:
            data = 0
        elif isinstance(input_files, list):
            data = 1
        if len(data_format) == 0 or len(result_format) == 0  or len(text) == 0 or len(fort) == 0 or data==0:
            result = '出错了，请仔细阅读操作流程(帮助文档.txt)后重试'
            with open('帮助文档.txt', 'w') as f:
                f.write("若问题还未解决，请查看\n文件投放规则：\n1.一组图片（数量不限）\n2.一个压缩包（仅可投放一个）\n\n文件的压缩包压缩方式为：\n1.点击要压缩文件所在的文件夹\n2.鼠标右键点击并选择“压缩为ZIP文件”即可\n3.不要进入文件夹中全选所有文件然后进行压缩\n希望这些可以帮助到你！\n\n                             ——由背水一战团队撰写")
            file_list.append('帮助文档.txt')
            arrow=1
        else:
            arrow=0
            if input_files[0].endswith('.zip'):
                with zipfile.ZipFile(input_files[0], 'r') as zip_ref:
                    zip_ref.extractall(destination_path)
                file_name_with_extension = os.path.basename(input_files[0])
                file_name_without_extension = os.path.splitext(file_name_with_extension)[0]
                rename_files(destination_path + '/{}'.format(file_name_without_extension), data_format)
                destination_path = destination_path + '/{}'.format(file_name_without_extension)
            else:
                # 遍历文件列表
                for source_file in input_files:
                    file_name = os.path.basename(source_file)
                    destination_file = os.path.join(destination_path, file_name)
                    shutil.copy(source_file, destination_file)
            file_format = "*" + str(data_format)
            file_list = glob.glob(os.path.join(destination_path, file_format))
        with open('results.txt', 'w') as f:
            f.write("当前评阅科目为：{}\n".format(fort))
        processed_advice, processed_grade = "评卷建议正在生成中，请您耐心等待...", "？"
        yield  "正在认真评阅中，请您耐心等待...", None, None, processed_advice, processed_grade
        for file in file_list:
            if flag==1:
                if arrow==0:
                    with open(file, 'rb') as f:
                        image_datas = f.read()
                    np_arr = np.frombuffer(image_datas, np.uint8)
                    image_datas = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                    processed_advices, processed_grade = process_files(fort, image_datas, text)
                    image_data = image_datas
                    processed_advice = "当前评阅科目为：{}\n".format(fort) + processed_advices
                if result_format == '逐一输出' and arrow==0:
                    with open(os.path.splitext(file)[0] + '.txt', 'w') as f:
                        f.write(processed_advice + '\n')
                        f.write(processed_grade)
                    result_list = glob.glob(os.path.join(destination_path, '*.txt'))
                    result ="评阅暂未完成，当前进度进度为{}/{}，文件（  *.txt）已更新，请您耐心等待！".format(len(result_list),len(file_list))
                    if len(result_list) == len(file_list):
                        yield '批量评阅完毕,请下载下方文件（  *.txt）查看结果!', result_list, image_data, processed_advices, processed_grade
                        time.sleep(5)
                        result,image_data, processed_advices,processed_grade= '批量评阅完毕,请下载下方文件（  *.txt）查看结果!',None,None,None
                    if flag==0:
                        yield '批量评阅已暂停，当前进度为{}/{},请下载下方文件（  *.txt）查看结果!'.format(len(result_list),len(file_list)), result_list, image_data, processed_advices, processed_grade
                        time.sleep(5)
                        result,image_data, processed_advices,processed_grade= '批量评阅已暂停，当前进度为{}/{},请下载下方文件（  *.txt）查看结果!'.format(len(result_list),len(file_list)),None,None,None
                    yield result, result_list, image_data, processed_advices,processed_grade
                elif result_format == '整合输出' and arrow==0:
                    with open('results.txt', 'a') as f:
                        f.write("第{}位同学的评卷建议以及建议得分如下：".format(i) + '\n')
                        f.write(processed_advices + '\n')
                        f.write(processed_grade + '\n\n')
                    result = "评阅暂未完成，当前进度进度为{}/{}，文件（results.txt）已更新，请您耐心等待！".format(i,len(file_list))
                    if i == len(file_list):
                        yield '批量评阅完毕,请下载下方文件（results.txt）查看结果!', 'results.txt', image_data, processed_advices,processed_grade
                        time.sleep(5)
                        result,image_data, processed_advices,processed_grade= '批量评阅完毕,请下载下方文件（results.txt）查看结果!',None,None,None
                    if flag == 0:
                        yield  '批量评阅已暂停，当前进度为{}/{},请下载下方文件（results.txt）查看结果!'.format(i,len(file_list)), 'results.txt', image_data, processed_advices,processed_grade
                        time.sleep(5)
                        result, image_data, processed_advices, processed_grade = '批量评阅已暂停，当前进度为{}/{},请下载下方文件（results.txt）查看结果!'.format(i,len(file_list)), None, None, None
                    yield result, 'results.txt', image_data, processed_advices,processed_grade
                elif arrow==1:
                    yield result, '帮助文档.txt', None, "请检查评阅科目、答题卡照片、标准答案、图片格式以及评阅结果输出格式选择是否正确！", "ERROR"
                i += 1
    except Exception:
        result = '出错了，请仔细阅读操作流程(帮助文档.txt)后重试'
        image_data, processed_advice, processed_grade = None,"请检查评阅科目、答题卡照片、标准答案、图片格式以及评阅结果输出格式选择是否正确！", "ERROR"
        with open('帮助文档.txt', 'w') as f:
            f.write("若问题还未解决，请查看\n文件投放规则：\n1.一组图片（数量不限）\n2.一个压缩包（仅可投放一个）\n\n文件的压缩包压缩方式为：\n1.点击要压缩文件所在的文件夹\n2.鼠标右键点击并选择“压缩为ZIP文件”即可\n3.不要进入文件夹中全选所有文件然后进行压缩\n希望这些可以帮助到你！\n\n                             ——由背水一战团队撰写")
        return result, '帮助文档.txt',image_data, processed_advice, processed_grade



with gr.Blocks(title='智能试卷评阅系统') as demo:
    with gr.Tab('精准分析'):
        gr.Markdown(
            """
            # 欢迎使用!            
            专业的教师评卷系统只为帮助热爱工作的你！

            对症下药，有的放矢。
            """)
        gr.Markdown("请输入考生的答题卡图片以及标准答案，本系统会自动给出评分建议以及建议得分。")
        format = gr.Dropdown(label="评阅科目选择处", choices=["政治", "历史", "地理", "生物", "语文", ""], type="value")
        with gr.Row():
            image = gr.Image(sources=["upload"], label="答题卡投放处")
            anwser = gr.Textbox(label="标准答案", lines=10, placeholder="请输入本题目的标准答案...")

        with gr.Row():
            with gr.Row():
                demo1 = gr.Button("示例展示")
                clear = gr.Button("清空内容")
            submit = gr.Button("开始生成")

        with gr.Row():
            advice = gr.Textbox(label="评卷建议", lines=10, max_lines=30, placeholder="点击“开始生成”即可查看...")
            score = gr.Label(label="建议得分")
        result_txt = gr.File(label="生成评估下载处")
        with gr.Accordion("精准分析说明"):
            with gr.Row():
                gr.Markdown(
                    """
                    # 本评分系统使用等级制计分
                    得分等级为：
                    - A：80-100分
                    - B：60-80分
                    - C：40-60分
                    - D：20-40分
                    - E：0-20分

                    使用该系统的老师可依次等级酌情给予对应的占比得分。

                    公式：本题最终得分=等级得分*本题总分数/100
                    """)

        submit.click(fn=submit_input, inputs=[format, image, anwser], outputs=[advice, score, result_txt])
        clear.click(fn=clear_input, inputs=[], outputs=[image, format, anwser])
        demo1.click(fn=demo_do, inputs=[], outputs=[format, image, anwser])
        gr.Markdown("本系统由背水一战团队训练提供")

    with gr.Tab('批量评阅'):
        gr.Markdown(
            """
            # 欢迎使用!
            专业的教师评卷系统只为帮助热爱工作的你！

            批量操作，提高效率。
            """)
        gr.Markdown(
            "请输入批量处理的考生答题卡图片或者压缩包以及标准答案并选择图片格式，本系统会自动批量更改并给出评分建议以及建议得分。")
        format = gr.Dropdown(label="评阅科目选择处", choices=["政治", "历史", "地理", "生物", "语文", ""], type="value")
        with gr.Row():
            with gr.Column():
                data_file = gr.Files(label="答题卡压缩包或者学生答题卡批量投放处")
                data_format = gr.Dropdown(label="图片格式选择处", choices=[".jpg", ".jpeg", ".png", ".bmp", ""],
                                          type="value")
            with gr.Column():
                anwser = gr.Textbox(label="标准答案", lines=10, max_lines=30, placeholder="请输入本题目的标准答案...")
                result_format = gr.Dropdown(label="评阅结果输出格式选择处", choices=["逐一输出", "整合输出", ""])
        with gr.Row():
            with gr.Row():
                demo1 = gr.Button("示例展示")
                clears = gr.Button("清空内容")
                submit = gr.Button("开始批量生成")
                stop = gr.Button("停止批阅工作")
        gr.Markdown("点击“开始批量生成”系统会自动生成评阅建议以及对应文档，生成过程中会有橘色方框亮起，您可在橘框内部实时查看评阅进度，生成结束下方则会显示“批量生成完毕!”且同时橘色方框熄灭。")
        result = gr.Label(label="生成完成标识")
        with gr.Row():
            image = gr.Image(sources=["upload"], label="答题卡显示处")
            advice = gr.Textbox(label="评卷建议", lines=8, max_lines=15,placeholder="点击“显示当前批改试卷”即可查看...")
            score = gr.Label(label="建议得分")
        result_txt = gr.Files(label="生成评估下载处")
        with gr.Accordion("批量评阅说明"):
            with gr.Row():
                with gr.Column():
                    gr.Markdown(
                        """
                        # 本评分系统使用等级制计分

                        得分等级为：
                        - A：80-100分                    
                        - B：60-80分                    
                        - C：40-60分                    
                        - D：20-40分                    
                        - E：0-20分

                        使用该系统的老师可依次等级酌情给予对应的占比得分。

                            公式：本题最终得分=等级得分*本题总分数/100
                        """)
                    gr.Markdown(
                        """
                        # 文件投放规则：

                        1.一组图片（数量不限）

                        2.一个压缩包（仅可投放一个）

                        """)
                with gr.Column():
                    gr.Markdown(
                        """
                        # 文件的压缩包压缩方式为：

                        1.点击要压缩文件所在的文件夹

                        2.鼠标右键点击并选择“压缩为ZIP文件”即可

                        3.不要进入文件夹中选择需要压缩的文件然后进行压缩                        
                        """)
                    gr.Markdown(
                        """                             
                        # 输出文件命名规则：

                        1.若选择“整合输出”模式，则输出结果为“results.txt”

                        2.若选择“逐一输出”模式，则

                        （1）若输入的文件为一组图片，则命名方式为“图片名称.txt”

                        （2）若输入的文件为一个压缩包，则命名方式类似于“学生答案 (1).txt”,

                           命名序号与压缩包内图片排序有关
                        """)
        clears.click(fn=clears_input, inputs=[], outputs=[data_file, format, anwser, data_format, result_format])
        submit.click(fn=process_file, inputs=[format, data_file, anwser, data_format, result_format],
                     outputs=[result, result_txt,image,advice, score])
        stop.click(fn=stop_do, inputs=[], outputs=[])
        demo1.click(fn=demos_do, inputs=[], outputs=[format, data_file, anwser, data_format, result_format])
        gr.Markdown("""
                    本系统由背水一战团队训练提供
                    """)
demo.launch()