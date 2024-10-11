import json
import pandas as pd
# 打开并读取txt文件
file_path = 'sps.txt'
company_info = []

with open(file_path, 'r', encoding='utf-8') as file:
    data = json.load(file)  # 读取整个JSON文件
    # 遍历 'hits' 列表，提取公司名称, hallAndLevel 和 firstBoothNumber
    for item in data['result']['hits']:
        company_name = item['exhibitor']['addressrdm'].get('companyName', 'Unknown')
        # 检查 'presentationLinks' 字段获取展厅和展位信息
        if item['exhibitor'].get('presentationLinks'):
            hall_and_level = item['exhibitor']['presentationLinks'][0].get('pstands', [{}])[0].get('hallAndLevel', 'Unknown')
            booth_number = item['exhibitor']['presentationLinks'][0].get('pstands', [{}])[0].get('firstBoothNumber', 'Unknown')
        else:
            hall_and_level = 'Unknown'
            booth_number = 'Unknown'
        
        company_info.append([company_name, hall_and_level, booth_number])

# 将信息导入到pandas的DataFrame中
df = pd.DataFrame(company_info, columns=['Company Name', 'Hall and Level', 'Booth Number'])

# 将DataFrame保存为Excel文件
excel_file_path = 'company_info.xlsx'
df.to_excel(excel_file_path, index=False)

print(f"Company information has been successfully exported to {excel_file_path}")
