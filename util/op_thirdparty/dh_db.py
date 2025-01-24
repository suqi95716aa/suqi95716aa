import datetime
from loguru import logger
from typing import Union, List, Dict, Tuple

from util.retry import a_retry
from models.database.user import UserInfo
from models.database.screen import ScreenInfo
from models.database.config import ConfigInfo
from models.database.template import TemplateInfo
from models.database.advise import FeedbackInfo

from sqlalchemy import select, update, and_, desc
from sqlalchemy.dialects.mysql import insert


@a_retry
async def dh_insert(session, item: Union[UserInfo, ConfigInfo, ScreenInfo, FeedbackInfo]) -> bool:
    """插入数据"""
    try:
        session.add(item)
        await session.commit()
        return True
    except Exception as error:
        print(f"dh_insert_userinfo save error：{error}")
        return False


@a_retry
async def dh_del(session, item: Union[UserInfo, ConfigInfo, ScreenInfo]) -> bool:
    """插入数据"""
    await session.delete(item)
    await session.commit()
    return True


@a_retry
async def dh_uid_exist_userinfo(session, Uid: str) -> Union[None, UserInfo]:
    """查询该username是否存在"""
    result = await session.execute(
        select(UserInfo).filter(UserInfo.uid == Uid, UserInfo.deleteTime == None)
    )
    return result.first()


@a_retry
async def dh_uname_pwd_exist_userinfo(session, username: str, password: str) -> Union[None, UserInfo]:
    """通过用户名密码查询该用户是否存在"""
    result = await session.execute(
        select(UserInfo).filter(UserInfo.username == username, UserInfo.password == password, UserInfo.deleteTime == None)
    )
    return result.first()


@a_retry
async def dh_uname_exist_userinfo(session, username: str) -> Union[None, UserInfo]:
    """通过用户名查询该用户是否存在"""
    result = await session.execute(
        select(UserInfo).filter(UserInfo.username == username, UserInfo.deleteTime == None)
    )
    return result.first()


@a_retry
async def dh_phone_exist_userinfo(session, phone: str) -> Union[None, UserInfo]:
    """通过用户名查询该用户是否存在"""
    result = await session.execute(
        select(UserInfo).filter(UserInfo.phone == phone, UserInfo.deleteTime == None)
    )
    return result.first()


@a_retry
async def dh_phone_pwd_exist_userinfo(session, phone: str, password: str) -> Union[None, UserInfo]:
    """通过用户名查询该用户是否存在"""
    result = await session.execute(
        select(UserInfo).filter(UserInfo.phone == phone, UserInfo.password == password, UserInfo.deleteTime == None)
    )
    return result.first()


@a_retry
async def dh_update_pwd_userinfo(session, phone: str, pwd: str) -> Union[bool]:
    """更新密码"""
    await session.execute(
        update(UserInfo).
            where(and_(UserInfo.phone == phone, UserInfo.deleteTime == None)).
            values({"password": pwd})
    )
    await session.commit()
    return True


@a_retry
async def dh_update_del_screeninfo(session, Uid: str, ScreenId: str) -> Union[bool]:
    """将删除时间更新"""
    await session.execute(
        update(ScreenInfo).
            where(and_(ScreenInfo.uid == Uid, ScreenInfo.screenId == ScreenId, ScreenInfo.deleteTime == None)).
            values({"deleteTime": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
    )
    await session.commit()
    return True


@a_retry
async def dh_screen_list_uid_screeninfo(session, Uid: str) -> List:
    """查询某个uid下的所有list"""
    result = await session.execute(select(ScreenInfo).filter(and_(ScreenInfo.uid == Uid, ScreenInfo.deleteTime == None)).order_by(desc(ScreenInfo.createTime)))

    return [
        item[0].to_dict()
        for item in sorted(result, key=lambda item: item[0].createTime, reverse=True)
    ]


@a_retry
async def dh_screen_exist_screeninfo(session, Uid: str, ScreenId: str, ScreenType: int) -> Tuple[ScreenInfo]:
    """查询某个场景是否存在及可用"""
    result = await session.execute(
        select(ScreenInfo).
            where(
            and_(ScreenInfo.uid == Uid, ScreenInfo.screenId == ScreenId, ScreenInfo.screenType == int(ScreenType), ScreenInfo.deleteTime == None))
    )
    return result.first()


@a_retry
async def dh_update_screeninfo(session, obj: Dict) -> bool:
    """场景配置更新"""
    screen_info_update_stmt = update(ScreenInfo).where(
        and_(
            ScreenInfo.uid == obj.get("Uid"),
            ScreenInfo.screenId == obj.get("ScreenId"),
        )
    ).values(
        screenName=obj.get("ScreenName"),
        screenDesc=obj.get("ScreenDesc"),
        screenQAConfig=obj.get("ScreenQAConfig"),
        updateTime=obj.get("UpdateTime")
    )
    await session.execute(screen_info_update_stmt)
    await session.commit()
    return True


@a_retry
async def dh_insert_if_not_exist_configinfo(session, req) -> bool:
    """场景中，相关配置信息存在则更新，不存在则插入"""
    await session.execute(
        insert(ConfigInfo).
        values(**req).
        on_duplicate_key_update(config=req.get("ConfigId"), updateTime=req.get("UpdateTime"))
    )
    await session.commit()
    return True


@a_retry
async def dh_config_exist_configinfo(session, Uid: str, ConfigId: str) -> Union[None, ConfigInfo]:
    """场景中，查找相关配置是否存在"""
    result = await session.execute(
        select(ConfigInfo).filter(and_(ConfigInfo.uid == Uid, ConfigInfo.configId == ConfigId, ConfigInfo.deleteTime == None))
    )
    return result.first()


@a_retry
async def dh_config_update_configinfo(session, obj: ConfigInfo) -> bool:
    """修改配置文件"""
    try:
        config_info_update_stmt = update(ConfigInfo).where(
            and_(
                ConfigInfo.uid == obj.uid,
                ConfigInfo.configId == obj.configId,
                ConfigInfo.label == obj.label
            )
        ).values(
            config=obj.config,
            updateTime=obj.updateTime
        )
        await session.execute(config_info_update_stmt)
        await session.commit()

        return True
    except Exception as error:
        logger.info(f"error:{error}")
        return False


@a_retry
async def dh_config_all_configinfo(session, Uid: str) -> List[ConfigInfo]:
    """查找用户名下所有的配置源"""
    result = await session.execute(
        select(ConfigInfo).filter(ConfigInfo.uid == Uid).order_by(desc(ConfigInfo.createTime))
    )
    return result.fetchall()


@a_retry
async def dh_tid_exist_templateinfo(session, tid: int) -> TemplateInfo:
    """查找template对应的map"""
    result = await session.execute(
        select(TemplateInfo).filter(TemplateInfo.Tid == int(tid))
    )
    return result.first()



