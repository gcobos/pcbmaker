To build the application: 

buildozer android debug deploy run


To sign app after release build

jarsigner -verbose -sigalg SHA1withRSA -digestalg SHA1 -keystore /home/drone/keys/leggedrobot.keystore ./bin/PCBMaker-1.0.0-release-unsigned.apk pcbmaker

