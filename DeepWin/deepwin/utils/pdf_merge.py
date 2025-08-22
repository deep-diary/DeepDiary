
import PyPDF2
import os

def merge_pdfs_advanced(file1, file2, output):
    # 检查输入文件是否存在
    if not os.path.exists(file1):
        print(f"错误：文件 {file1} 不存在")
        return
    if not os.path.exists(file2):
        print(f"错误：文件 {file2} 不存在")
        return
    
    try:
        # 创建PDF合并器
        merger = PyPDF2.PdfMerger()
        
        # 添加要合并的PDF文件
        merger.append(file1)
        merger.append(file2)
        
        # 写入输出文件
        with open(output, "wb") as out:
            merger.write(out)
        
        print(f"PDF文件已成功合并到: {output}")
        
    except Exception as e:
        print(f"合并PDF时发生错误: {e}")
    finally:
        merger.close()

# 使用示例
if __name__ == "__main__":
    merge_pdfs_advanced('doc1.pdf', 'doc2.pdf', 'combined.pdf')
