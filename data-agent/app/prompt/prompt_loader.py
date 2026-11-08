from pathlib import Path

# 加载指定文件内容
def load_prompt(name: str):
    # 要加载的文件路径
    prompt_path = Path(__file__).parents[2] /'prompts'/f'{name}.prompt'

    # 返回读取的文件内容
    return prompt_path.read_text(encoding='utf-8')

# 测试
if __name__ == '__main__':
    print(load_prompt('correct_sql'))
