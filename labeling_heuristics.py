import re


class Labeling:

    def __init__(self, file):
        self.log = []
        self.output = []
        self.script = {}
        self.js = {}
        with open(file, 'r') as f:
            self.log = f.readlines()

    # ---------------------------------------
    # collect script id, url
    # ---------------------------------------
    def identify_script(self):
        for line in self.log:
            id_pa = re.compile('(?<=^\$)\d+')
            url_pa = re.compile('(^\$\d+:")(.*?(?="))')
            child_id_pa = re.compile('(^\$\d+:)(\d+(?=:))')
            id_found = re.search(id_pa, line)
            if id_found:
                id = id_found.group(0)
                url_found = re.search(url_pa, line)
                child_id_found = re.search(child_id_pa, line)
                if url_found:
                    url = url_found.group(2).replace('https\\', 'https')
                    url = url.replace('http\\', 'http')
                    self.script[id] = url
                if child_id_found:
                    child_id = id
                    self.script[id] = self.script[child_id_found.group(2)]
                    # if id in self.script.keys():
                    #     self.script[child_id] =

    def split_log(self):
        id = 0
        id_pa = re.compile(r'(?<=!)\d+')
        for line in self.log:
            if line.startswith('!'):
                id_found = re.search(id_pa, line)
                if id_found:
                    id = id_found.group(0)
                    if id not in self.js.keys():
                        self.js[id] = []
            if id:
                self.js[id].append(line)

    # ---------------------------------------
    # v8 doesn't log ['fillStyle', 'strokeStyle'], searching in source code won't work for obfuscated code
    # ---------------------------------------
    def determine_canvas(self, value):
            canvas_text = 0
            canvas_toDataURL = 0
            for line in value:
                if line.startswith('$'):
                    continue
                if any(method in line for method in ['fillText', 'strokeText']):
                    canvas_text = 1
                if any(method in line for method in ['toDataURL', 'getImageData']):
                    canvas_toDataURL = 1
                if any(method in line for method in ['save', 'restore', 'addEventListener']) and \
                        any(word in line for word in ['{HTMLCanvasElement}', '{Canvas', 'Canvas}']):
                    print('false', 'non-fp calls on canvas element', line)
                    return False
            if canvas_text * canvas_toDataURL:
                print('canvas-fp identified')
                return True

    def determine_webrtc(self, value):
        webrtc_create = 0
        webrtc_on = 0
        for line in value:
            if line.startswith('$'):
                continue
            if any(method in line for method in ['createDataChannel', 'createOffer']):
                webrtc_create = 1
            if any(method in line for method in ['onicecandidate', 'localDescription']):
                webrtc_on = 1
        if webrtc_create and webrtc_on:
            print('webrtc-fp identified')
            return True

    def determine_canvas_font(self, value):
        fonts = set()
        font_pa = re.compile(r'(?<={CanvasRenderingContext2D}:").*?(?=")')
        call_num = 0
        for line in value:
            if line.startswith('$'):
                continue
            if all(method in line for method in ['{CanvasRenderingContext2D}', 'px']):
                font = re.search(font_pa, line).group(0)
                fonts.add(str(font))
            if 'measureText' in line:
                call_num += 1
        if len(fonts) > 20 and call_num > 20:
            print('canvas-font-fp identified')
            return True
        return False

    def determine_audio(self, value):
        for line in value:
            if line.startswith('$'):
                continue
            if any(method in line for method in ['createOscillator', 'createDynamicsCompressor', 'destination',
                                                 'startRendering', 'oncomplete']) and 'Audio' in line:
                print('audio-fp identified')
                return True

    def if_fp(self):
        self.identify_script()
        self.split_log()
        for key, value in self.js.items():
            result  = {}
            if key not in self.script.keys():
                print(key, value)
            result[self.script[key]] = []
            if self.determine_canvas(value):
                result[self.script[key]].append('canvas')
            if self.determine_webrtc(value):
                result[self.script[key]].append('webrtc')
            if self.determine_audio(value):
                result[self.script[key]].append('audio')
            if self.determine_canvas_font(value):
                result[self.script[key]].append('canvasfont')
            if result[self.script[key]]:
                self.output.append(result)
        return self.output



