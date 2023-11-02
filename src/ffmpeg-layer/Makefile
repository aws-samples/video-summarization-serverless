build-FFMpegLayer: 
	mkdir -p $(ARTIFACTS_DIR)/bin
	wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz -P $(ARTIFACTS_DIR)/bin/ 
	wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz.md5  -P $(ARTIFACTS_DIR)/bin/ 
	tar xvf $(ARTIFACTS_DIR)/bin/ffmpeg-release-amd64-static.tar.xz -C $(ARTIFACTS_DIR)/bin/
	mv $(ARTIFACTS_DIR)/bin/ffmpeg*/ffmpeg $(ARTIFACTS_DIR)/bin/ffmpeg*/ffprobe $(ARTIFACTS_DIR)/bin/