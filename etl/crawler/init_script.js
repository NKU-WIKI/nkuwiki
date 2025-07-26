// 删除webdriver属性
Object.defineProperty(navigator, 'webdriver', {
    get: () => undefined,
});

// 模拟Chrome特性
window.navigator.chrome = {
    runtime: {},
    app: {
        InstallState: {
            DISABLED: 'disabled',
            INSTALLED: 'installed',
            NOT_INSTALLED: 'not_installed'
        },
        RunningState: {
            CANNOT_RUN: 'cannot_run',
            READY_TO_RUN: 'ready_to_run',
            RUNNING: 'running'
        },
        getDetails: function() {},
        getIsInstalled: function() {},
        installState: function() {
            return 'installed';
        },
        isInstalled: true,
        runningState: function() {
            return 'running';
        }
    }
};

// 模拟插件
Object.defineProperty(navigator, 'plugins', {
    get: () => [
        {
            0: {type: "application/x-google-chrome-pdf"},
            description: "Portable Document Format",
            filename: "internal-pdf-viewer",
            length: 1,
            name: "Chrome PDF Plugin"
        }
    ],
});

// 模拟语言
Object.defineProperty(navigator, 'languages', {
    get: () => ['zh-CN', 'zh', 'en-US', 'en'],
});

// 模拟设备内存
Object.defineProperty(navigator, 'deviceMemory', {
    get: () => 8,
});

// 模拟硬件并发性
Object.defineProperty(navigator, 'hardwareConcurrency', {
    get: () => 8,
});

// 模拟 WebGL
Object.defineProperty(HTMLCanvasElement.prototype, 'toDataURL', {
    get: function() {
        return function() {
            return 'data:image/png;base64,';
        }
    }
});

// 模拟 Connection 信息
Object.defineProperty(navigator, 'connection', {
    get: () => ({
        downlink: 10 + Math.random() * 5,
        effectiveType: '4g',
        rtt: 50 + Math.floor(Math.random() * 100),
        saveData: false
    })
});

// 模拟 Permissions
Object.defineProperty(navigator, 'permissions', {
    get: () => ({
        query: function() {
            return Promise.resolve({ state: 'granted' });
        }
    })
});

// 屏蔽 Automation 检测
delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;

// 添加更多的浏览器指纹模拟
(() => {
    // 模拟 WebGL 渲染器信息
    const getParameter = WebGLRenderingContext.prototype.getParameter;
    WebGLRenderingContext.prototype.getParameter = function(parameter) {
        if (parameter === 37445) {
            return 'Intel Inc.';
        }
        if (parameter === 37446) {
            return 'Intel Iris OpenGL Engine';
        }
        return getParameter.apply(this, arguments);
    };

    // 模拟更真实的 canvas 指纹
    const oldGetContext = HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext = function(type) {
        const context = oldGetContext.apply(this, arguments);
        if (type === '2d') {
            const oldGetImageData = context.getImageData;
            context.getImageData = function() {
                const imageData = oldGetImageData.apply(this, arguments);
                return imageData;
            };
        }
        return context;
    };

    // 模拟音频上下文
    const audioContext = window.AudioContext || window.webkitAudioContext;
    if (audioContext) {
        const origGetChannelData = audioContext.prototype.getChannelData;
        audioContext.prototype.getChannelData = function() {
            const results = origGetChannelData.apply(this, arguments);
            return results;
        };
    }

    // 添加更多的浏览器特性
    Object.defineProperties(navigator, {
        vendor: { get: () => 'Google Inc.' },
        platform: { get: () => 'Win32' },
        maxTouchPoints: { get: () => 0 },
    });

    // 模拟电池状态
    if (navigator.getBattery) {
        navigator.getBattery = function() {
            return Promise.resolve({
                charging: true,
                chargingTime: 0,
                dischargingTime: Infinity,
                level: 1
            });
        };
    }

    // 屏蔽自动化检测特征
    const objectToInspect = window;
    const result = [];
    for (let prop in objectToInspect) {
        if (prop.match(/.+_.+_(Array|Promise|Symbol)/)) {
            result.push(prop);
        }
    }
    result.forEach(key => delete objectToInspect[key]);

    // 模拟更真实的屏幕分辨率
    Object.defineProperties(screen, {
        width: { get: () => 1920 },
        height: { get: () => 1080 },
        availWidth: { get: () => 1920 },
        availHeight: { get: () => 1040 },
        colorDepth: { get: () => 24 },
        pixelDepth: { get: () => 24 }
    });

    // 修改 toString 方法以避免检测
    const oldToString = Function.prototype.toString;
    Function.prototype.toString = function() {
        if (this === Function.prototype.toString) return oldToString.call(this);
        if (this === Function.prototype.bind) return 'function bind() { [native code] }';
        return oldToString.call(this);
    };
})();

// 覆盖更多WebGL属性
WebGLRenderingContext.prototype.getParameter = function(parameter) {
    if (parameter === 37445) return 'Google Inc. (NVIDIA)';
    if (parameter === 37446) return 'ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Ti Direct3D11 vs_5_0 ps_5_0, D3D11)';
    return WebGLRenderingContext.prototype.getParameter.apply(this, [parameter]);
};

// 覆盖更多navigator属性
Object.defineProperty(navigator, 'userAgent', {
    get: () => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'
});

// 新浪财经特定检测点覆盖
delete window.__fxdriver_unwrapped;
delete window._Selenium_IDE_Recorder;
delete window._selenium;
delete window.callPhantom;
delete window.phantom;

// 添加更多自动化特征字符串删除
const pattern = /(selenium|webdriver|phantomjs|appium|automation|cdc_)/i;
Object.getOwnPropertyNames(window).forEach(prop => {
    if (pattern.test(prop)) {
        delete window[prop];
    }
});

// 覆盖新浪财经使用的屏幕检测
Object.defineProperty(window.screen, 'availHeight', { 
    get: () => 1080 
});
Object.defineProperty(window.screen, 'availWidth', { 
    get: () => 1920 
});

// 模拟新浪财经的鼠标轨迹检测
const originalMove = MouseEvent.prototype.move;
MouseEvent.prototype.move = function(x, y) {
    const jitterX = x + Math.random() * 3 - 1.5;
    const jitterY = y + Math.random() * 3 - 1.5;
    return originalMove.call(this, jitterX, jitterY);
}; 