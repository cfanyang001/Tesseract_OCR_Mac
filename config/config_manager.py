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
        self.last_config_file = os.path.join(config_dir, "last_config.json")
        
        # 确保配置目录存在
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
        
        # 加载所有配置
        self.load_all_configs()
        
        # 加载最后使用的配置
        self.load_last_config()
    
    def load_all_configs(self):
        """加载所有配置文件"""
        try:
            # 获取配置目录下的所有json文件
            config_files = [f for f in os.listdir(self.config_dir) 
                           if f.endswith('.json') and f != "last_config.json" and os.path.isfile(os.path.join(self.config_dir, f))]
            
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
    
    def load_last_config(self):
        """加载最后使用的配置"""
        try:
            if os.path.exists(self.last_config_file):
                with open(self.last_config_file, 'r', encoding='utf-8') as f:
                    last_config = json.load(f)
                    config_name = last_config.get('name', '默认配置')
                    
                    if config_name in self.configs:
                        self.current_config = config_name
                        logger.info(f"已加载最后使用的配置: {config_name}")
                    else:
                        logger.warning(f"最后使用的配置 {config_name} 不存在，使用默认配置")
        except Exception as e:
            logger.error(f"加载最后使用的配置失败: {e}")
    
    def save_last_config(self):
        """保存最后使用的配置"""
        try:
            with open(self.last_config_file, 'w', encoding='utf-8') as f:
                json.dump({'name': self.current_config}, f, ensure_ascii=False, indent=2)
            logger.info(f"已保存最后使用的配置: {self.current_config}")
        except Exception as e:
            logger.error(f"保存最后使用的配置失败: {e}")
    
    def get_default_config(self):
        """获取默认配置"""
        return {
            "global": {
                "language": "中文简体",
                "theme": "暗色",
                "log_level": "info"
            },
            "ocr": {
                "language": "中文简体",
                "psm": "3",
                "oem": "3",
                "preprocess": True,
                "autocorrect": False,
                "recognition_mode": "标准模式",
                "result_cache_size": 10,
                "screen_area": {
                    "x": 0,
                    "y": 0,
                    "width": 1,
                    "height": 1,
                    "is_selected": False
                }
            },
            "monitor": {
                "interval": "2",
                "match_mode": "包含匹配",
                "auto_retry": True,
                "retry_interval": "1"
            },
            "actions": {
                "delay": "0.5",
                "retries": "1",
                "timeout": "10",
                "confirm_action": True
            },
            "task": {
                "max_concurrent": "3",
                "priority_mode": "先进先出",
                "auto_restart": True
            },
            "logs": {
                "retention_days": "7",
                "max_size": "10MB",
                "export_format": "txt"
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
    
    def get_section_config(self, section, config_name=None):
        """获取指定配置的特定部分
        
        Args:
            section: 配置部分名称，如"ocr", "monitor"等
            config_name: 配置名称，如果为None则使用当前配置
            
        Returns:
            配置部分字典
        """
        config = self.get_config(config_name)
        return config.get(section, {})
    
    def update_section_config(self, section, section_config, config_name=None):
        """更新配置的特定部分
        
        Args:
            section: 配置部分名称，如"ocr", "monitor"等
            section_config: 配置部分内容
            config_name: 配置名称，如果为None则使用当前配置
            
        Returns:
            bool: 是否成功更新
        """
        name = config_name or self.current_config
        if name not in self.configs:
            logger.warning(f"配置 {name} 不存在，无法更新")
            return False
        
        # 更新配置部分
        self.configs[name][section] = section_config
        logger.info(f"已更新配置 {name} 的 {section} 部分")
        return True
    
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
            
            # 如果是当前配置，保存为最后使用的配置
            if config_name == self.current_config:
                self.save_last_config()
            
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
                
                # 如果删除的是当前配置，切换到默认配置
                if config_name == self.current_config:
                    self.current_config = "默认配置"
                    self.save_last_config()
                
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
            # 保存最后使用的配置
            self.save_last_config()
            logger.info(f"当前配置已设置为: {config_name}")
            return True
        else:
            logger.warning(f"配置不存在: {config_name}")
            return False
