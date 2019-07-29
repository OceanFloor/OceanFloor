# External Tools Used by OceanFloor

## FFmpeg

![](./images/ffmpeg.png)

##### As Officially Described

> FFmpeg is the leading multimedia framework, able to decode, encode, transcode, mux, demux, stream, filter and play pretty much anything that humans and machines have created.

##### Used For...

Rendering videos - applying the effects chosen by the users.
The effects are applied by running commands in FFmpeg's [`ffmpeg.exe`](https://www.ffmpeg.org/ffmpeg.html) command line tool.

##### Links

- [Home Page](https://www.ffmpeg.org/)
- [About FFmpeg](https://www.ffmpeg.org/about.html)

## SQLite

![](./images/sqlite.png)

##### As Officially Described

> SQLite is a self-contained, high-reliability, embedded, full-featured, public-domain, SQL database engine. SQLite is the most used database engine in the world.

##### Used For...

Saving the current state of OceanFloor projects. [OceanFloor save files](./save-file-structure.md) (`.oceanfloor`) are SQLite database files that allow saving the project along with all the chosen effects and returning to it later.

##### Links

- [Home Page](https://www.sqlite.org/)
- [About SQLite](https://www.sqlite.org/about.html)

## YouTube Data API

![](./images/youtube_api.png)

##### As Officially Described

> With the YouTube Data API, you can add a variety of YouTube features to your application. Use the API to upload videos, manage playlists and subscriptions, update channel settings, and more.

##### Used For...

Uploading videos to users' YouTube channels from within OceanFloor, after rendering.

##### Links

- [Home Page](https://developers.google.com/youtube/v3/)

---

**[Back to the Documentation](../documentation.md)**

**[Back to the README](../readme.md)**
