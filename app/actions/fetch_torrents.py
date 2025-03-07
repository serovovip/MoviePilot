from typing import Optional, List

from pydantic import Field

from app.actions import BaseAction
from app.chain.search import SearchChain
from app.log import logger
from app.schemas import ActionParams, ActionContext, MediaType


class FetchTorrentsParams(ActionParams):
    """
    获取站点资源参数
    """
    name: str = Field(None, description="资源名称")
    year: Optional[int] = Field(None, description="年份")
    type: Optional[str] = Field(None, description="资源类型 (电影/电视剧)")
    season: Optional[int] = Field(None, description="季度")
    sites: Optional[List[int]] = Field([], description="站点列表")


class FetchTorrentsAction(BaseAction):
    """
    搜索站点资源
    """

    _torrents = []

    def __init__(self):
        super().__init__()
        self.searchchain = SearchChain()

    @property
    def name(self) -> str:
        return "获取站点资源"

    @property
    def description(self) -> str:
        return "根据关键字搜索站点种子资源"

    @property
    def success(self) -> bool:
        return True if self._torrents else False

    async def execute(self, params: FetchTorrentsParams, context: ActionContext) -> ActionContext:
        """
        搜索站点，获取资源列表
        """
        torrents = self.searchchain.search_by_title(title=params.name, sites=params.sites)
        for torrent in torrents:
            if params.year and torrent.meta_info.year != params.year:
                continue
            if params.type and torrent.media_info and torrent.media_info.type != MediaType(params.type):
                continue
            if params.season and torrent.meta_info.begin_season != params.season:
                continue
            # 识别媒体信息
            torrent.media_info = self.chain.recognize_media(torrent.meta_info)
            if not torrent.media_info:
                logger.warning(f"{torrent.torrent_info.title} 未识别到媒体信息")
                continue
            self._torrents.append(torrent)

        if self._torrents:
            context.torrents.extend(self._torrents)
            logger.info(f"搜索到 {len(self._torrents)} 条资源")

        self.job_done()
        return context
