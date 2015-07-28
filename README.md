# Docker Factory

This is an experimental buildsystem for Docker images based on Debian.

I built this because I didn't find anything better, didn't want to rely on existing Docker Hub images, and didn't want to update everything manually.

Since debian package versions are quite stable the idea is to keep this as a cronjob to automatically rebuild and/or update images as needed.

In production this would be accompanied by scripts to check for running Docker containers with outdated images and ideally a suite of tests.

### Current Features

 * Rebuild containers if updates are available from debian repositories (compares installed versions with repo versions)
 * Add config files in a completely seperate layer for quick rebuilds on config changes
 * Similar feature to "FROM", where images can be based on other images packages, but can add additional files

### Ideas

 * Currently my private registry is hardcoded, would be nice to have this configurable
 * Error handling and config/source validation should be added, currently completely relying on the script just crashing if something goes wrong
 * Build-Logs: Instead of throwing away output of debootstrap and apt it would be nice to have logfiles
 * Maybe move the whole buildsystem itself into a Docker container, to isolate it from the hostsystem in various steps
 * Minor updates: Based on number of updates and/or size it would be a nice thing to use dist-upgrades on images instead of rebuilds, even though with modern disks and network connections it doesn't really matter.
 * Progress indicator?

