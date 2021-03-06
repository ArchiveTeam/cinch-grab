import time
import os
import os.path
import shutil
import glob

from seesaw.project import *
from seesaw.config import *
from seesaw.item import *
from seesaw.task import *
from seesaw.pipeline import *
from seesaw.externalprocess import *
from seesaw.tracker import *

DATA_DIR = "data"
USER_AGENT = "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/533.20.25 (KHTML, like Gecko) Version/5.0.4 Safari/533.20.27"
VERSION = "20120821.02"

class PrepareDirectories(SimpleTask):
  def __init__(self):
    SimpleTask.__init__(self, "PrepareDirectories")

  def process(self, item):
    item_name = item["item_name"]
    dirname = "/".join(( DATA_DIR, item_name ))

    if os.path.isdir(dirname):
      shutil.rmtree(dirname)

    os.makedirs(dirname + "/files")

    item["item_dir"] = dirname
    item["data_dir"] = DATA_DIR
    item["warc_file_base"] = "cinch.fm-range-%s-%s" % (item_name, time.strftime("%Y%m%d-%H%M%S"))

class MoveFiles(SimpleTask):
  def __init__(self):
    SimpleTask.__init__(self, "MoveFiles")

  def process(self, item):
    os.rename("%(item_dir)s/%(warc_file_base)s.warc.gz" % item,
              "%(data_dir)s/%(warc_file_base)s.warc.gz" % item)

    shutil.rmtree("%(item_dir)s" % item)

class DeleteFiles(SimpleTask):
  def __init__(self):
    SimpleTask.__init__(self, "DeleteFiles")

  def process(self, item):
    os.unlink("%(data_dir)s/%(warc_file_base)s.warc.gz" % item)

def calculate_item_id(item):
  playlist_xmls = glob.glob("%(item_dir)s/files/cinch.fm/cinchplaylist.aspx*" % item)
  n = len(playlist_xmls)
  if n == 0:
    return "null"
  else:
    return playlist_xmls[0] + "-" + playlist_xmls[n-1]


project = Project(
  title = "Cinch.FM",
  project_html = """
    <img class="project-logo" alt="Cinch.FM logo" src="http://archiveteam.org/images/thumb/6/6e/Cinch-logo.png/120px-Cinch-logo.png" height="50" />
    <h2>Cinch.FM <span class="links"><a href="http://cinch.fm/">Website</a> &middot; <a href="http://tracker.archiveteam.org/cinch/">Leaderboard</a></span></h2>
    <p>Cinch.FM will remove all data on October 20, 2012.</p>
  """,
  utc_deadline = datetime.datetime(2012,10,20, 23,59,0)
)

pipeline = Pipeline(
  GetItemFromTracker("http://tracker.archiveteam.org/cinch", downloader, VERSION),
  PrepareDirectories(),
  WgetDownload([ "./wget-lua",
      "-U", USER_AGENT,
      "-nv",
      "-o", ItemInterpolation("%(item_dir)s/wget.log"),
      "--directory-prefix", ItemInterpolation("%(item_dir)s/files"),
      "--force-directories",
      "--adjust-extension",
      "-e", "robots=off",
      "--page-requisites", "--span-hosts",
      "--lua-script", "cinch-range.lua",
      "--warc-file", ItemInterpolation("%(item_dir)s/%(warc_file_base)s"),
      "--warc-header", "operator: Archive Team",
      "--warc-header", "cinch-fm-dld-script-version: " + VERSION,
      "--warc-header", ItemInterpolation("cinch-fm-range: %(item_name)s"),
      ItemInterpolation("http://cinch.fm/cinchplaylist.aspx?RecordingID=%(item_name)s0"),
      ItemInterpolation("http://cinch.fm/cinchplaylist.aspx?RecordingID=%(item_name)s1"),
      ItemInterpolation("http://cinch.fm/cinchplaylist.aspx?RecordingID=%(item_name)s2"),
      ItemInterpolation("http://cinch.fm/cinchplaylist.aspx?RecordingID=%(item_name)s3"),
      ItemInterpolation("http://cinch.fm/cinchplaylist.aspx?RecordingID=%(item_name)s4"),
      ItemInterpolation("http://cinch.fm/cinchplaylist.aspx?RecordingID=%(item_name)s5"),
      ItemInterpolation("http://cinch.fm/cinchplaylist.aspx?RecordingID=%(item_name)s6"),
      ItemInterpolation("http://cinch.fm/cinchplaylist.aspx?RecordingID=%(item_name)s7"),
      ItemInterpolation("http://cinch.fm/cinchplaylist.aspx?RecordingID=%(item_name)s8"),
      ItemInterpolation("http://cinch.fm/cinchplaylist.aspx?RecordingID=%(item_name)s9")
    ],
    max_tries = 2,
    accept_on_exit_code = [ 0, 4, 6, 8 ],
  ),
  PrepareStatsForTracker(
    defaults = { "downloader": downloader, "version": VERSION },
    file_groups = {
      "data": [ ItemInterpolation("%(item_dir)s/%(warc_file_base)s.warc.gz") ]
    },
    id_function = calculate_item_id
  ),
  MoveFiles(),
  LimitConcurrent(1,
    RsyncUpload(
      target = ConfigInterpolation("fos.textfiles.com::cinch/%s/", downloader),
      target_source_path = ItemInterpolation("%(data_dir)s/"),
      files = [
        ItemInterpolation("%(warc_file_base)s.warc.gz")
      ],
      extra_args = [
        "--partial-dir", ".rsync-tmp"
      ]
    ),
  ),
  SendDoneToTracker(
    tracker_url = "http://tracker.archiveteam.org/cinch",
    stats = ItemValue("stats")
  ),
  DeleteFiles()
)

