# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import os
import time
from pathlib import Path

from unittest import mock, SkipTest
import pytest
from ...testing import TempFATFS
from ...utils.filemanip import (
    save_json,
    load_json,
    fname_presuffix,
    fnames_presuffix,
    hash_rename,
    check_forhash,
    _parse_mount_table,
    _cifs_table,
    on_cifs,
    copyfile,
    copyfiles,
    ensure_list,
    simplify_list,
    check_depends,
    split_filename,
    get_related_files,
    indirectory,
    loadpkl,
    savepkl,
    path_resolve,
    write_rst_list,
    emptydirs,
)


def _ignore_atime(stat):
    return stat[:7] + stat[8:]


@pytest.mark.parametrize(
    "filename, split",
    [
        ("foo.nii", ("", "foo", ".nii")),
        ("foo.nii.gz", ("", "foo", ".nii.gz")),
        ("foo.niml.dset", ("", "foo", ".niml.dset")),
        ("/usr/local/foo.nii.gz", ("/usr/local", "foo", ".nii.gz")),
        ("../usr/local/foo.nii", ("../usr/local", "foo", ".nii")),
        ("/usr/local/foo.a.b.c.d", ("/usr/local", "foo.a.b.c", ".d")),
        ("/usr/local/", ("/usr/local", "", "")),
    ],
)
def test_split_filename(filename, split):
    res = split_filename(filename)
    assert res == split


def test_fname_presuffix():
    fname = "foo.nii"
    pth = fname_presuffix(fname, "pre_", "_post", "/tmp")
    assert pth == "/tmp/pre_foo_post.nii"
    fname += ".gz"
    pth = fname_presuffix(fname, "pre_", "_post", "/tmp")
    assert pth == "/tmp/pre_foo_post.nii.gz"
    pth = fname_presuffix(fname, "pre_", "_post", "/tmp", use_ext=False)
    assert pth == "/tmp/pre_foo_post"


def test_fnames_presuffix():
    fnames = ["foo.nii", "bar.nii"]
    pths = fnames_presuffix(fnames, "pre_", "_post", "/tmp")
    assert pths == ["/tmp/pre_foo_post.nii", "/tmp/pre_bar_post.nii"]


@pytest.mark.parametrize(
    "filename, newname",
    [
        ("foobar.nii", "foobar_0xabc123.nii"),
        ("foobar.nii.gz", "foobar_0xabc123.nii.gz"),
    ],
)
def test_hash_rename(filename, newname):
    new_name = hash_rename(filename, "abc123")
    assert new_name == newname


def test_check_forhash():
    fname = "foobar"
    orig_hash = "_0x4323dbcefdc51906decd8edcb3327943"
    hashed_name = f"{fname}{orig_hash}.nii"
    result, hash = check_forhash(hashed_name)
    assert result
    assert hash == [orig_hash]
    result, hash = check_forhash("foobar.nii")
    assert not result
    assert hash is None


@pytest.fixture()
def _temp_analyze_files(tmpdir):
    """Generate temporary analyze file pair."""
    orig_img = tmpdir.join("orig.img")
    orig_hdr = tmpdir.join("orig.hdr")
    orig_img.open("w+").close()
    orig_hdr.open("w+").close()
    return str(orig_img), str(orig_hdr)


@pytest.fixture()
def _temp_analyze_files_prime(tmpdir):
    """Generate temporary analyze file pair."""
    orig_img = tmpdir.join("orig_prime.img")
    orig_hdr = tmpdir.join("orig_prime.hdr")
    orig_img.open("w+").close()
    orig_hdr.open("w+").close()
    return orig_img.strpath, orig_hdr.strpath


def test_copyfile(_temp_analyze_files):
    orig_img, orig_hdr = _temp_analyze_files
    pth, fname = os.path.split(orig_img)
    new_img = os.path.join(pth, "newfile.img")
    new_hdr = os.path.join(pth, "newfile.hdr")
    copyfile(orig_img, new_img)
    assert os.path.exists(new_img)
    assert os.path.exists(new_hdr)


def test_copyfile_true(_temp_analyze_files):
    orig_img, orig_hdr = _temp_analyze_files
    pth, fname = os.path.split(orig_img)
    new_img = os.path.join(pth, "newfile.img")
    new_hdr = os.path.join(pth, "newfile.hdr")
    # Test with copy=True
    copyfile(orig_img, new_img, copy=True)
    assert os.path.exists(new_img)
    assert os.path.exists(new_hdr)


def test_copyfiles(_temp_analyze_files, _temp_analyze_files_prime):
    orig_img1, orig_hdr1 = _temp_analyze_files
    orig_img2, orig_hdr2 = _temp_analyze_files_prime
    pth, fname = os.path.split(orig_img1)
    new_img1 = os.path.join(pth, "newfile.img")
    new_hdr1 = os.path.join(pth, "newfile.hdr")
    pth, fname = os.path.split(orig_img2)
    new_img2 = os.path.join(pth, "secondfile.img")
    new_hdr2 = os.path.join(pth, "secondfile.hdr")
    copyfiles([orig_img1, orig_img2], [new_img1, new_img2])
    assert os.path.exists(new_img1)
    assert os.path.exists(new_hdr1)
    assert os.path.exists(new_img2)
    assert os.path.exists(new_hdr2)


def test_linkchain(_temp_analyze_files):
    if os.name != "posix":
        return
    orig_img, orig_hdr = _temp_analyze_files
    pth, fname = os.path.split(orig_img)
    new_img1 = os.path.join(pth, "newfile1.img")
    new_hdr1 = os.path.join(pth, "newfile1.hdr")
    new_img2 = os.path.join(pth, "newfile2.img")
    new_hdr2 = os.path.join(pth, "newfile2.hdr")
    new_img3 = os.path.join(pth, "newfile3.img")
    new_hdr3 = os.path.join(pth, "newfile3.hdr")
    copyfile(orig_img, new_img1)
    assert os.path.islink(new_img1)
    assert os.path.islink(new_hdr1)
    copyfile(new_img1, new_img2, copy=True)
    assert not os.path.islink(new_img2)
    assert not os.path.islink(new_hdr2)
    assert not os.path.samefile(orig_img, new_img2)
    assert not os.path.samefile(orig_hdr, new_hdr2)
    copyfile(new_img1, new_img3, copy=True, use_hardlink=True)
    assert not os.path.islink(new_img3)
    assert not os.path.islink(new_hdr3)
    assert os.path.samefile(orig_img, new_img3)
    assert os.path.samefile(orig_hdr, new_hdr3)


def test_recopy(_temp_analyze_files):
    # Re-copying with the same parameters on an unchanged file should be
    # idempotent
    #
    # Test for copying from regular files and symlinks
    orig_img, orig_hdr = _temp_analyze_files
    pth, fname = os.path.split(orig_img)
    img_link = os.path.join(pth, "imglink.img")
    new_img = os.path.join(pth, "newfile.img")
    new_hdr = os.path.join(pth, "newfile.hdr")
    copyfile(orig_img, img_link)
    for copy in (True, False):
        for use_hardlink in (True, False):
            for hashmethod in ("timestamp", "content"):
                kwargs = {
                    "copy": copy,
                    "use_hardlink": use_hardlink,
                    "hashmethod": hashmethod,
                }
                # Copying does not preserve the original file's timestamp, so
                # we may delete and re-copy, if the test is slower than a clock
                # tick
                if copy and not use_hardlink and hashmethod == "timestamp":
                    continue

                copyfile(orig_img, new_img, **kwargs)
                img_stat = _ignore_atime(os.stat(new_img))
                hdr_stat = _ignore_atime(os.stat(new_hdr))
                copyfile(orig_img, new_img, **kwargs)
                err_msg = "Regular - OS: {}; Copy: {}; Hardlink: {}".format(
                    os.name, copy, use_hardlink
                )
                assert img_stat == _ignore_atime(os.stat(new_img)), err_msg
                assert hdr_stat == _ignore_atime(os.stat(new_hdr)), err_msg
                os.unlink(new_img)
                os.unlink(new_hdr)

                copyfile(img_link, new_img, **kwargs)
                img_stat = _ignore_atime(os.stat(new_img))
                hdr_stat = _ignore_atime(os.stat(new_hdr))
                copyfile(img_link, new_img, **kwargs)
                err_msg = "Symlink - OS: {}; Copy: {}; Hardlink: {}".format(
                    os.name, copy, use_hardlink
                )
                assert img_stat == _ignore_atime(os.stat(new_img)), err_msg
                assert hdr_stat == _ignore_atime(os.stat(new_hdr)), err_msg
                os.unlink(new_img)
                os.unlink(new_hdr)


def test_copyfallback(_temp_analyze_files):
    if os.name != "posix":
        return
    orig_img, orig_hdr = _temp_analyze_files
    pth, imgname = os.path.split(orig_img)
    pth, hdrname = os.path.split(orig_hdr)
    try:
        fatfs = TempFATFS()
    except OSError:
        raise SkipTest("Fuse mount failed. copyfile fallback tests skipped.")

    with fatfs as fatdir:
        tgt_img = os.path.join(fatdir, imgname)
        tgt_hdr = os.path.join(fatdir, hdrname)
        for copy in (True, False):
            for use_hardlink in (True, False):
                copyfile(orig_img, tgt_img, copy=copy, use_hardlink=use_hardlink)
                assert os.path.exists(tgt_img)
                assert os.path.exists(tgt_hdr)
                assert not os.path.islink(tgt_img)
                assert not os.path.islink(tgt_hdr)
                assert not os.path.samefile(orig_img, tgt_img)
                assert not os.path.samefile(orig_hdr, tgt_hdr)
                os.unlink(tgt_img)
                os.unlink(tgt_hdr)


def test_get_related_files(_temp_analyze_files):
    orig_img, orig_hdr = _temp_analyze_files

    related_files = get_related_files(orig_img)
    assert orig_img in related_files
    assert orig_hdr in related_files

    related_files = get_related_files(orig_hdr)
    assert orig_img in related_files
    assert orig_hdr in related_files


def test_get_related_files_noninclusive(_temp_analyze_files):
    orig_img, orig_hdr = _temp_analyze_files

    related_files = get_related_files(orig_img, include_this_file=False)
    assert orig_img not in related_files
    assert orig_hdr in related_files

    related_files = get_related_files(orig_hdr, include_this_file=False)
    assert orig_img in related_files
    assert orig_hdr not in related_files


@pytest.mark.parametrize(
    "filename, expected",
    [
        ("foo.nii", ["foo.nii"]),
        (["foo.nii"], ["foo.nii"]),
        (("foo", "bar"), ["foo", "bar"]),
        (12.34, None),
    ],
)
def test_ensure_list(filename, expected):
    x = ensure_list(filename)
    assert x == expected


@pytest.mark.parametrize(
    "list, expected", [(["foo.nii"], "foo.nii"), (["foo", "bar"], ["foo", "bar"])]
)
def test_simplify_list(list, expected):
    x = simplify_list(list)
    assert x == expected


def test_check_depends(tmpdir):
    def touch(fname):
        with open(fname, "a"):
            os.utime(fname, None)

    dependencies = [tmpdir.join(str(i)).strpath for i in range(3)]
    targets = [tmpdir.join(str(i)).strpath for i in range(3, 6)]

    # Targets newer than dependencies
    for dep in dependencies:
        touch(dep)
    time.sleep(1)
    for tgt in targets:
        touch(tgt)
    assert check_depends(targets, dependencies)

    # Targets older than newest dependency
    time.sleep(1)
    touch(dependencies[0])
    assert not check_depends(targets, dependencies)

    # Missing dependency
    os.unlink(dependencies[0])
    try:
        check_depends(targets, dependencies)
    except OSError:
        pass
    else:
        assert False, "Should raise OSError on missing dependency"


def test_json(tmpdir):
    # Simple roundtrip test of json files, just a sanity check.
    adict = dict(a="one", c="three", b="two")
    name = tmpdir.join("test.json").strpath
    save_json(name, adict)  # save_json closes the file
    new_dict = load_json(name)
    os.unlink(name)
    assert sorted(adict.items()) == sorted(new_dict.items())


@pytest.mark.parametrize(
    "file, length, expected_files",
    [
        ("/path/test.img", 3, ["/path/test.hdr", "/path/test.img", "/path/test.mat"]),
        ("/path/test.hdr", 3, ["/path/test.hdr", "/path/test.img", "/path/test.mat"]),
        ("/path/test.BRIK", 2, ["/path/test.BRIK", "/path/test.HEAD"]),
        ("/path/test.HEAD", 2, ["/path/test.BRIK", "/path/test.HEAD"]),
        ("/path/foo.nii", 2, ["/path/foo.nii", "/path/foo.mat"]),
    ],
)
def test_related_files(file, length, expected_files):
    related_files = get_related_files(file)

    assert len(related_files) == length

    for ef in expected_files:
        assert ef in related_files


MOUNT_OUTPUTS = (
    # Linux, no CIFS
    (
        r"""sysfs on /sys type sysfs (rw,nosuid,nodev,noexec,relatime)
proc on /proc type proc (rw,nosuid,nodev,noexec,relatime)
udev on /dev type devtmpfs (rw,nosuid,relatime,size=8121732k,nr_inodes=2030433,mode=755)
devpts on /dev/pts type devpts (rw,nosuid,noexec,relatime,gid=5,mode=620,ptmxmode=000)
tmpfs on /run type tmpfs (rw,nosuid,noexec,relatime,size=1628440k,mode=755)
/dev/nvme0n1p2 on / type ext4 (rw,relatime,errors=remount-ro,data=ordered)
securityfs on /sys/kernel/security type securityfs (rw,nosuid,nodev,noexec,relatime)
tmpfs on /dev/shm type tmpfs (rw,nosuid,nodev)
tmpfs on /sys/fs/cgroup type tmpfs (ro,nosuid,nodev,noexec,mode=755)
cgroup on /sys/fs/cgroup/systemd type cgroup (rw,nosuid,nodev,noexec,relatime,xattr,release_agent=/lib/systemd/systemd-cgroups-agent,name=systemd)
pstore on /sys/fs/pstore type pstore (rw,nosuid,nodev,noexec,relatime)
efivarfs on /sys/firmware/efi/efivars type efivarfs (rw,nosuid,nodev,noexec,relatime)
cgroup on /sys/fs/cgroup/cpu,cpuacct type cgroup (rw,nosuid,nodev,noexec,relatime,cpu,cpuacct)
cgroup on /sys/fs/cgroup/freezer type cgroup (rw,nosuid,nodev,noexec,relatime,freezer)
cgroup on /sys/fs/cgroup/pids type cgroup (rw,nosuid,nodev,noexec,relatime,pids)
cgroup on /sys/fs/cgroup/cpuset type cgroup (rw,nosuid,nodev,noexec,relatime,cpuset)
systemd-1 on /proc/sys/fs/binfmt_misc type autofs (rw,relatime,fd=26,pgrp=1,timeout=0,minproto=5,maxproto=5,direct)
hugetlbfs on /dev/hugepages type hugetlbfs (rw,relatime)
debugfs on /sys/kernel/debug type debugfs (rw,relatime)
mqueue on /dev/mqueue type mqueue (rw,relatime)
fusectl on /sys/fs/fuse/connections type fusectl (rw,relatime)
/dev/nvme0n1p1 on /boot/efi type vfat (rw,relatime,fmask=0077,dmask=0077,codepage=437,iocharset=iso8859-1,shortname=mixed,errors=remount-ro)
/dev/nvme0n1p2 on /var/lib/docker/aufs type ext4 (rw,relatime,errors=remount-ro,data=ordered)
gvfsd-fuse on /run/user/1002/gvfs type fuse.gvfsd-fuse (rw,nosuid,nodev,relatime,user_id=1002,group_id=1002)
""",
        0,
        [],
    ),
    # OS X, no CIFS
    (
        r"""/dev/disk2 on / (hfs, local, journaled)
devfs on /dev (devfs, local, nobrowse)
map -hosts on /net (autofs, nosuid, automounted, nobrowse)
map auto_home on /home (autofs, automounted, nobrowse)
map -fstab on /Network/Servers (autofs, automounted, nobrowse)
/dev/disk3s2 on /Volumes/MyBookData (hfs, local, nodev, nosuid, journaled)
afni:/elrond0 on /Volumes/afni (nfs)
afni:/var/www/INCOMING on /Volumes/INCOMING (nfs)
afni:/fraid on /Volumes/afni (nfs, asynchronous)
boromir:/raid.bot on /Volumes/raid.bot (nfs)
elros:/volume2/AFNI_SHARE on /Volumes/AFNI_SHARE (nfs)
map -static on /Volumes/safni (autofs, automounted, nobrowse)
map -static on /Volumes/raid.top (autofs, automounted, nobrowse)
/dev/disk1s3 on /Volumes/Boot OS X (hfs, local, journaled, nobrowse)
""",
        0,
        [],
    ),
    # Non-zero exit code
    ("", 1, []),
    # Variant of Linux example with CIFS added manually
    (
        r"""sysfs on /sys type sysfs (rw,nosuid,nodev,noexec,relatime)
proc on /proc type proc (rw,nosuid,nodev,noexec,relatime)
udev on /dev type devtmpfs (rw,nosuid,relatime,size=8121732k,nr_inodes=2030433,mode=755)
devpts on /dev/pts type devpts (rw,nosuid,noexec,relatime,gid=5,mode=620,ptmxmode=000)
tmpfs on /run type tmpfs (rw,nosuid,noexec,relatime,size=1628440k,mode=755)
/dev/nvme0n1p2 on / type ext4 (rw,relatime,errors=remount-ro,data=ordered)
securityfs on /sys/kernel/security type securityfs (rw,nosuid,nodev,noexec,relatime)
tmpfs on /dev/shm type tmpfs (rw,nosuid,nodev)
tmpfs on /sys/fs/cgroup type tmpfs (ro,nosuid,nodev,noexec,mode=755)
cgroup on /sys/fs/cgroup/systemd type cgroup (rw,nosuid,nodev,noexec,relatime,xattr,release_agent=/lib/systemd/systemd-cgroups-agent,name=systemd)
pstore on /sys/fs/pstore type pstore (rw,nosuid,nodev,noexec,relatime)
efivarfs on /sys/firmware/efi/efivars type efivarfs (rw,nosuid,nodev,noexec,relatime)
cgroup on /sys/fs/cgroup/cpu,cpuacct type cgroup (rw,nosuid,nodev,noexec,relatime,cpu,cpuacct)
cgroup on /sys/fs/cgroup/freezer type cgroup (rw,nosuid,nodev,noexec,relatime,freezer)
cgroup on /sys/fs/cgroup/pids type cgroup (rw,nosuid,nodev,noexec,relatime,pids)
cgroup on /sys/fs/cgroup/cpuset type cgroup (rw,nosuid,nodev,noexec,relatime,cpuset)
systemd-1 on /proc/sys/fs/binfmt_misc type autofs (rw,relatime,fd=26,pgrp=1,timeout=0,minproto=5,maxproto=5,direct)
hugetlbfs on /dev/hugepages type hugetlbfs (rw,relatime)
debugfs on /sys/kernel/debug type debugfs (rw,relatime)
mqueue on /dev/mqueue type mqueue (rw,relatime)
fusectl on /sys/fs/fuse/connections type fusectl (rw,relatime)
/dev/nvme0n1p1 on /boot/efi type vfat (rw,relatime,fmask=0077,dmask=0077,codepage=437,iocharset=iso8859-1,shortname=mixed,errors=remount-ro)
/dev/nvme0n1p2 on /var/lib/docker/aufs type ext4 (rw,relatime,errors=remount-ro,data=ordered)
gvfsd-fuse on /run/user/1002/gvfs type fuse.gvfsd-fuse (rw,nosuid,nodev,relatime,user_id=1002,group_id=1002)
""",
        0,
        [],
    ),
    # Variant of OS X example with CIFS added manually
    (
        r"""/dev/disk2 on / (hfs, local, journaled)
devfs on /dev (devfs, local, nobrowse)
afni:/elrond0 on /Volumes/afni (cifs)
afni:/var/www/INCOMING on /Volumes/INCOMING (nfs)
afni:/fraid on /Volumes/afni/fraid (nfs, asynchronous)
boromir:/raid.bot on /Volumes/raid.bot (nfs)
elros:/volume2/AFNI_SHARE on /Volumes/AFNI_SHARE (nfs)
""",
        0,
        [("/Volumes/afni/fraid", "nfs"), ("/Volumes/afni", "cifs")],
    ),
    # From Windows: docker run --rm -it -v C:\:/data busybox mount
    (
        r"""overlay on / type overlay (rw,relatime,lowerdir=/var/lib/docker/overlay2/l/26UTYITLF24YE7KEGTMHUNHPPG:/var/lib/docker/overlay2/l/SWGNP3T2EEB4CNBJFN3SDZLXHP,upperdir=/var/lib/docker/overlay2/a4c54ab1aa031bb5a14a424abd655510521e183ee4fa4158672e8376c89df394/diff,workdir=/var/lib/docker/overlay2/a4c54ab1aa031bb5a14a424abd655510521e183ee4fa4158672e8376c89df394/work)
proc on /proc type proc (rw,nosuid,nodev,noexec,relatime)
tmpfs on /dev type tmpfs (rw,nosuid,size=65536k,mode=755)
devpts on /dev/pts type devpts (rw,nosuid,noexec,relatime,gid=5,mode=620,ptmxmode=666)
sysfs on /sys type sysfs (ro,nosuid,nodev,noexec,relatime)
tmpfs on /sys/fs/cgroup type tmpfs (ro,nosuid,nodev,noexec,relatime,mode=755)
cpuset on /sys/fs/cgroup/cpuset type cgroup (ro,nosuid,nodev,noexec,relatime,cpuset)
cpu on /sys/fs/cgroup/cpu type cgroup (ro,nosuid,nodev,noexec,relatime,cpu)
cpuacct on /sys/fs/cgroup/cpuacct type cgroup (ro,nosuid,nodev,noexec,relatime,cpuacct)
blkio on /sys/fs/cgroup/blkio type cgroup (ro,nosuid,nodev,noexec,relatime,blkio)
memory on /sys/fs/cgroup/memory type cgroup (ro,nosuid,nodev,noexec,relatime,memory)
devices on /sys/fs/cgroup/devices type cgroup (ro,nosuid,nodev,noexec,relatime,devices)
freezer on /sys/fs/cgroup/freezer type cgroup (ro,nosuid,nodev,noexec,relatime,freezer)
net_cls on /sys/fs/cgroup/net_cls type cgroup (ro,nosuid,nodev,noexec,relatime,net_cls)
perf_event on /sys/fs/cgroup/perf_event type cgroup (ro,nosuid,nodev,noexec,relatime,perf_event)
net_prio on /sys/fs/cgroup/net_prio type cgroup (ro,nosuid,nodev,noexec,relatime,net_prio)
hugetlb on /sys/fs/cgroup/hugetlb type cgroup (ro,nosuid,nodev,noexec,relatime,hugetlb)
pids on /sys/fs/cgroup/pids type cgroup (ro,nosuid,nodev,noexec,relatime,pids)
cgroup on /sys/fs/cgroup/systemd type cgroup (ro,nosuid,nodev,noexec,relatime,name=systemd)
mqueue on /dev/mqueue type mqueue (rw,nosuid,nodev,noexec,relatime)
//10.0.75.1/C on /data type cifs (rw,relatime,vers=3.02,sec=ntlmsspi,cache=strict,username=filo,domain=MSI,uid=0,noforceuid,gid=0,noforcegid,addr=10.0.75.1,file_mode=0755,dir_mode=0755,iocharset=utf8,nounix,serverino,mapposix,nobrl,mfsymlinks,noperm,rsize=1048576,wsize=1048576,echo_interval=60,actimeo=1)
/dev/sda1 on /etc/resolv.conf type ext4 (rw,relatime,data=ordered)
/dev/sda1 on /etc/hostname type ext4 (rw,relatime,data=ordered)
/dev/sda1 on /etc/hosts type ext4 (rw,relatime,data=ordered)
shm on /dev/shm type tmpfs (rw,nosuid,nodev,noexec,relatime,size=65536k)
devpts on /dev/console type devpts (rw,nosuid,noexec,relatime,gid=5,mode=620,ptmxmode=666)
proc on /proc/bus type proc (ro,relatime)
proc on /proc/fs type proc (ro,relatime)
proc on /proc/irq type proc (ro,relatime)
proc on /proc/sys type proc (ro,relatime)
proc on /proc/sysrq-trigger type proc (ro,relatime)
tmpfs on /proc/kcore type tmpfs (rw,nosuid,size=65536k,mode=755)
tmpfs on /proc/timer_list type tmpfs (rw,nosuid,size=65536k,mode=755)
tmpfs on /proc/sched_debug type tmpfs (rw,nosuid,size=65536k,mode=755)
tmpfs on /proc/scsi type tmpfs (ro,relatime)
tmpfs on /sys/firmware type tmpfs (ro,relatime)
""",
        0,
        [("/data", "cifs")],
    ),
    # From @yarikoptic - added blank lines to test for resilience
    (
        r"""/proc on /proc type proc (rw,relatime)
sysfs on /sys type sysfs (rw,nosuid,nodev,noexec,relatime)
tmpfs on /dev/shm type tmpfs (rw,relatime)
devpts on /dev/pts type devpts (rw,nosuid,noexec,relatime,gid=5,mode=620,ptmxmode=666)

devpts on /dev/ptmx type devpts (rw,nosuid,noexec,relatime,gid=5,mode=620,ptmxmode=666)

""",
        0,
        [],
    ),
)


@pytest.mark.parametrize("output, exit_code, expected", MOUNT_OUTPUTS)
def test_parse_mount_table(output, exit_code, expected):
    assert _parse_mount_table(exit_code, output) == expected


def test_cifs_check():
    assert isinstance(_cifs_table, list)
    assert isinstance(on_cifs("/"), bool)
    fake_table = [("/scratch/tmp", "ext4"), ("/scratch", "cifs")]
    cifs_targets = [
        ("/scratch/tmp/x/y", False),
        ("/scratch/tmp/x", False),
        ("/scratch/x/y", True),
        ("/scratch/x", True),
        ("/x/y", False),
        ("/x", False),
        ("/", False),
    ]

    orig_table = _cifs_table[:]
    _cifs_table[:] = []

    for target, _ in cifs_targets:
        assert on_cifs(target) is False

    _cifs_table.extend(fake_table)
    for target, expected in cifs_targets:
        assert on_cifs(target) is expected

    _cifs_table[:] = []
    _cifs_table.extend(orig_table)


def test_indirectory(tmpdir):
    tmpdir.chdir()

    os.makedirs("subdir1/subdir2")
    sd1 = os.path.abspath("subdir1")
    sd2 = os.path.abspath("subdir1/subdir2")

    assert os.getcwd() == tmpdir.strpath
    with indirectory("/"):
        assert os.getcwd() == "/"
    assert os.getcwd() == tmpdir.strpath
    with indirectory("subdir1"):
        assert os.getcwd() == sd1
        with indirectory("subdir2"):
            assert os.getcwd() == sd2
            with indirectory(".."):
                assert os.getcwd() == sd1
                with indirectory("/"):
                    assert os.getcwd() == "/"
                assert os.getcwd() == sd1
            assert os.getcwd() == sd2
        assert os.getcwd() == sd1
    assert os.getcwd() == tmpdir.strpath
    try:
        with indirectory("subdir1"):
            raise ValueError("Erroring out of context")
    except ValueError:
        pass
    assert os.getcwd() == tmpdir.strpath


def test_pklization(tmpdir):
    tmpdir.chdir()

    exc = Exception("There is something wrong here")
    savepkl("./except.pkz", exc)
    newexc = loadpkl("./except.pkz")

    assert exc.args == newexc.args
    assert os.getcwd() == tmpdir.strpath


class Pickled:
    def __getstate__(self):
        return self.__dict__


class PickledBreaker:
    def __setstate__(self, d):
        raise Exception


def test_versioned_pklization(tmpdir):
    tmpdir.chdir()

    obj = Pickled()
    savepkl("./pickled.pkz", obj, versioning=True)

    with pytest.raises(Exception):
        with mock.patch(
            "nipype.utils.tests.test_filemanip.Pickled", PickledBreaker
        ), mock.patch("nipype.__version__", "0.0.0"):
            loadpkl("./pickled.pkz")


def test_unversioned_pklization(tmpdir):
    tmpdir.chdir()

    obj = Pickled()
    savepkl("./pickled.pkz", obj)

    with pytest.raises(Exception):
        with mock.patch("nipype.utils.tests.test_filemanip.Pickled", PickledBreaker):
            loadpkl("./pickled.pkz")


def test_path_strict_resolve(tmpdir):
    """Check the monkeypatch to test strict resolution of Path."""
    tmpdir.chdir()

    # Default strict=False should work out of the box
    testfile = Path("somefile.txt")
    resolved = "%s/somefile.txt" % tmpdir
    assert str(path_resolve(testfile)) == resolved
    # Strict keyword is always allowed
    assert str(path_resolve(testfile, strict=False)) == resolved

    # Switching to strict=True must raise FileNotFoundError (also in Python2)
    with pytest.raises(FileNotFoundError):
        path_resolve(testfile, strict=True)

    # If the file is created, it should not raise
    open("somefile.txt", "w").close()
    assert str(path_resolve(testfile, strict=True)) == resolved


@pytest.mark.parametrize("save_versioning", [True, False])
def test_pickle(tmp_path, save_versioning):
    testobj = "iamateststr"
    pickle_fname = str(tmp_path / "testpickle.pklz")
    savepkl(pickle_fname, testobj, versioning=save_versioning)
    outobj = loadpkl(pickle_fname)
    assert outobj == testobj


@pytest.mark.parametrize(
    "items,expected",
    [
        ("", " \n\n"),
        ("A string", " A string\n\n"),
        (["A list", "Of strings"], " A list\n Of strings\n\n"),
        (None, TypeError),
    ],
)
def test_write_rst_list(tmp_path, items, expected):
    if items is not None:
        assert write_rst_list(items) == expected
    else:
        with pytest.raises(expected):
            write_rst_list(items)


def nfs_unlink(pathlike, *, dir_fd=None):
    if dir_fd is None:
        path = Path(pathlike)
        deleted = path.with_name(".nfs00000000")
        path.rename(deleted)
    else:
        os.rename(pathlike, ".nfs1111111111", src_dir_fd=dir_fd, dst_dir_fd=dir_fd)


def test_emptydirs_dangling_nfs(tmp_path):
    busyfile = tmp_path / "base" / "subdir" / "busyfile"
    busyfile.parent.mkdir(parents=True)
    busyfile.touch()

    with mock.patch("os.unlink") as mocked:
        mocked.side_effect = nfs_unlink
        emptydirs(tmp_path / "base")

    assert Path.exists(tmp_path / "base")
    assert not busyfile.exists()
    assert busyfile.parent.exists()  # Couldn't remove
