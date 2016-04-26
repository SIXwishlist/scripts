#!/usr/bin/env bash
###
#
# diskimg.sh
# Creates a raw file that can be used for loop mounts or disk images.
#
###

# Default image size is 4GB
size=4096
# Default two-partition setup
partitions=2
# Default mount after image creation
domount=1

if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root." 1>&2
    exit 1
fi

while getopts :s:p:n:h opt; do
    case $opt in
    h|\?)
        echo "Usage: diskimg.sh [-s size] [-p partitions] [-n] output-file"
        echo "  output-file: full path to image that should be created"
        echo ""
        echo "Optional arguments:"
        echo "  -s   SIZE of the output image, in megabytes (default 4096)"
        echo "  -p   PARTITIONS: 1 for a single large partition, 2 to include a FAT32 boot partition first (default)"
        echo "  -n   NO MOUNT: do not mount the image after creation"
        echo ""
        exit 0
        ;;
    s) size=$OPTARG
        ;;
    p) partitions=$OPTARG
        ;;
    n) domount=0
        ;;
    :)
       echo "Option -$OPTARG requires an argument" >&2
       exit 1
    esac
done
shift $((OPTIND-1))
if [[ "$@" == "" ]]; then
  echo "Requires file path"
  exit 1
fi
filepath="$@"

# Create empty image file
echo "Writing image file..."
dd if=/dev/zero of="$filepath" bs=1M count=$size

# Mount image as loopback
loopdev="$(losetup -f)"
losetup $loopdev "$filepath"
if [[ $partitions == 2 ]]; then
    echo -e "n\np\n1\n\n+100M\nt\nc\nn\np\n2\n\n\nw\n" | fdisk $loopdev
elif [[ $partitions == 1 ]]; then
    echo -e "n\np\n1\n\n\nw\n" | fdisk $loopdev
fi
partprobe $loopdev

if [[ $domount == 1 ]]; then
  if [ ! -d "/tmp/root" ]; then
      mkdir -p /tmp/root
  fi
  if [[ $partitions == 1 ]]; then
      mkfs.ext4 "${loopdev}p1"
      mount "${loopdev}p1" /tmp/root
  elif [[ $partitions == 2 ]]; then
      mkfs.vfat "${loopdev}p1"
      mkfs.ext4 "${loopdev}p2"
      mount "${loopdev}p2" /tmp/root
      mkdir -p /tmp/root/boot
      mount "${loopdev}p1" /tmp/root/boot
  fi
  echo "Empty image ready at /tmp/root."
fi

exit 0
