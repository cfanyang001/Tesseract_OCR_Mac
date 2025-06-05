import os
import json
from loguru import logger

class ConfigManager:
    """配置管理器类，用于处理配置的保存和加载"""
    
    def __init__(self, config_dir="config"):
        """初始化配置管理器
        
        Args:
            config_dir: 配置文件存储目录
        """
        self.config_dir = config_dir
        self.configs = {}
        self.current_config = "默认配置"
        
        # 确保配置目录存在
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
        
        # 加载默认配置
        self.load_all_configs()
    
    def load_all_configs(self):
        """加载所有配置文件"""
        try:
            # 获取配置目录下的所有json文件
            config_files = [f for f in os.listdir(self.config_dir) 
                           if f.endswith('.json') and os.path.isfile(os.path.join(self.config_dir, f))]
            
            # 加载每个配置文件
            for file in config_files:
                config_name = os.path.splitext(file)[0]
                config_path = os.path.join(self.config_dir, file)
                
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        self.configs[config_name] = json.load(f)
                    logger.info(f"已加载配置: {config_name}")
                except Exception as e:
                    logger.error(f"加载配置 {config_name} 失败: {e}")
            
            # 如果没有找到配置，创建默认配置
            if not self.configs:
                self.configs["默认配置"] = self.get_default_config()
                self.save_config("默认配置")
                logger.info("创建了默认配置")
        
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            # 确保至少有默认配置
            self.configs["默认配置"] = self.get_default_config()
    
    def get_default_config(self):
        """获取默认配置"""
        return {
            "ocr": {
                "language": "eng",
                "psm": "3",
                "oem": "3"
            },
            "monitor": {
                "interval": "2",
                "match_mode": "包含匹配"
            },
            "actions": {
                "delay": "0.5",
                "retries": "1"
            }
        }
    
    def get_config(self, config_name=None):
        """获取指定名称的配置
        
        Args:
            config_name: 配置名称，如果为None则返回当前配置
            
        Returns:
            配置字典
        """
        name = config_name or self.current_config
        
        # 如果配置不存在，返回默认配置
        if name not in self.configs:
            logger.warning(f"配置 {name} 不存在，返回默认配置")
            return self.configs.get("默认配置", self.get_default_config())
        
        return self.configs[name]
    
    def save_config(self, config_name, config_data=None):
        """保存配置
        
        Args:
            config_name: 配置名称
            config_data: 配置数据，如果为None则保存当前配置
        """
        try:
            data = config_data or self.configs.get(config_name)
            if not data:
                logger.error(f"没有找到配置数据: {config_name}")
                return False
            
            # 更新内存中的配置
            self.configs[config_name] = data
            
            # 保存到文件
            config_path = os.path.join(self.config_dir, f"{config_name}.json")
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"配置已保存: {config_name}")
            return True
        
        except Exception as e:
            logger.error(f"保存配置 {config_name} 失败: {e}")
            return False
    
    def delete_config(self, config_name):
        """删除配置
        
        Args:
            config_name: 配置名称
            
        Returns:
            bool: 是否成功删除
        """
        # 不允许删除默认配置
        if config_name == "默认配置":
            logger.warning("不能删除默认配置")
            return False
        
        try:
            # 从内存中删除
            if config_name in self.configs:
                del self.configs[config_name]
            
            # 删除文件
            config_path = os.path.join(self.config_dir, f"{config_name}.json")
            if os.path.exists(config_path):
                os.remove(config_path)
                logger.info(f"配置已删除: {config_name}")
                return True
            else:
                logger.warning(f"配置文件不存在: {config_name}")
                return False
        
        except Exception as e:
            logger.error(f"删除配置 {config_name} 失败: {e}")
            return False
    
    def get_all_config_names(self):
        """获取所有配置名称
        
        Returns:
            list: 配置名称列表
        """
        return list(self.configs.keys())
    
    def set_current_config(self, config_name):
        """设置当前配置
        
        Args:
            config_name: 配置名称
            
        Returns:
            bool: 是否成功设置
        """
        if config_name in self.configs:
            self.current_config = config_name
            logger.info(f"当前配置已设置为: {config_name}")
            return True
        else:
            logger.warning(f"配置不存在: {config_name}")
            return False
