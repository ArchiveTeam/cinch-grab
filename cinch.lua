dofile("table_show.lua")
dofile("urlcode.lua")

read_file = function(file)
  local f = io.open(file)
  local data = f:read("*all")
  f:close()
  return data
end

parse_form = function(html)
  fields = {}
  for name, value in string.gmatch(html, "<input type=\"hidden\"[^>]* name=\"([^\"]+)\"[^>]* value=\"([^\"]*)\"") do
    fields[name] = value
  end
  return fields
end

next_button_strings = {
  "ctl00$ContentMain$CinchSingle$Replies1$PagerRepliesBottom$lbtnNext",
  "ctl00$ContentMain$More1$lbtnMore",
  "ctl00$ContentMain$PagerFollowersTop$lbtnNext",
  "ctl00$ContentMain$PagerUsersTop$lbtnNext"
}

url_count = 0

wget.callbacks.get_urls = function(file, url, is_css, iri)
  local urls = {}

  -- progress message
  url_count = url_count + 1
  if url_count % 25 == 0 then
    print("Downloaded #"..url_count)
  end

  if string.match(url, "^http://cinch\.fm/[^.]+$") or string.match(url, "^http://cinch\.fm/[^.]+\.aspx$") then
    -- possible pagination
    html = read_file(file)

    for i, next_button_string in pairs(next_button_strings) do
      if string.match(html, next_button_string) then
        -- there is a next page: click the button!
        args = parse_form(html)
        args["__EVENTTARGET"] = next_button_string

        table.insert(urls, { url=url, post_data=cgilua.urlcode.encodetable(fields), link_expect_html=1 })

        break
      end
    end

    -- is this the user page?
    user_url = string.match(url, "^(http://cinch\.fm/[^./]+)$")
    if user_url then
      table.insert(urls, { url=(user_url..".rss") })
    end

    -- find permalinks to tracks
    for track_url in string.gmatch(html, "<a href=\"(http://cinch\.fm/[^\"]+/[0-9]+)\" title=\"Permalink\"") do
      track_id = string.match(track_url, "[0-9]+$")
      table.insert(urls, { url=track_url, link_expect_html=1 })
      table.insert(urls, { url=(track_url..".mp3") })
      table.insert(urls, { url=("http://cinch.fm/cinchplaylist.aspx?RecordingID="..track_id) })

      album_url = string.match(track_url, "^(http://cinch\.fm/[^./]+/[^./]+)/[0-9]+$")
      if album_url then
        -- track is part of an album
        table.insert(urls, { url=album_url, link_expect_html=1 })
        table.insert(urls, { url=(album_url..".rss") })
      end
    end
  end

  return urls
end

