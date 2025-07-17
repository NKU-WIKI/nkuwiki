#首先安装依赖包pip install -r requirements.txt

#从大模型api中获取答案：
 ##coze串行调用请运行process_excel_single.py
 ##coze并行调用请运行process_excel_parallel.py
 ##硅基流动并行调用请运行siliconflow_api.py

#如果coze调用api有太多错误发生：请运行retry_failed_answers.py
 硅基流动暂时没做错误debug

#评估答案：请运行evaluate.py

 ##修改ecxel_path指向excel文本路径
 
 ##如果你的Excel文件中列名不是"参考答案"和"ai答案"，你可以在调用 evaluate_answers 函数时指定列名：similarities = evaluate_answers(excel_path, reference_col='你的参考答案列名', ai_col='你的AI答案列名')

备注：所有文档均需自行修改input_path/output_path等，调用api的url自行修改
