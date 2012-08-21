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
    print(" - Downloaded "..url_count.." URLs")
  end

  if string.match(url, "^http://cinch\.fm/cinchplaylist\.aspx[?]RecordingID=[0-9]+$") then
    -- a playlist, add the urls in the XML file
    xml = read_file(file)

    u = string.match(xml, "<showimage>(http://[^<]+)")
    if u then
      table.insert(urls, { url=u })
    end
    u = string.match(xml, "<imagelink>(http://[^<]+)")
    if u then
      table.insert(urls, { url=u, link_expect_html=1 })
      table.insert(urls, { url=(u..".mp3") })

      u = string.match(u, "^(http://cinch\.fm/[^./]+/[^./]+)/[0-9]+$")
      if u then
        -- an album
        table.insert(urls, { url=u, link_expect_html=1 })
        table.insert(urls, { url=(u..".rss") })
      end
    end

  elseif string.match(url, "^http://cinch\.fm/[^.]+$") or string.match(url, "^http://cinch\.fm/[^.]+\.aspx$") then
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
  end

  return urls
end

