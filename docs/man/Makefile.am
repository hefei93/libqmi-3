
dist_man_MANS = \
	qmicli.1 \
	qmi-network.1

# List of all source files which affect the output of --help-all
QMICLI_SOURCES_WITH_HELP = \
	$(top_srcdir)/src/qmicli/qmicli.c \
	$(top_srcdir)/src/qmicli/qmicli-dms.c \
	$(top_srcdir)/src/qmicli/qmicli-nas.c \
	$(top_srcdir)/src/qmicli/qmicli-wds.c \
	$(top_srcdir)/src/qmicli/qmicli-pbm.c \
	$(top_srcdir)/src/qmicli/qmicli-uim.c

# Depend only in the source files, not in the actual program, so that the
# manpage doesn't get rebuilt when building from a tarball
# Also, make sure that the qmicli.1 file is always generated, even when help2man
# is not available
qmicli.1: $(QMICLI_SOURCES_WITH_HELP)
	$(AM_V_GEN) \
		$(HELP2MAN) \
			--output=$@ \
			--name='Control QMI devices' \
			--help-option='--help-all' \
			--libtool \
			$(top_builddir)/src/qmicli/qmicli || \
		touch $@

# Depend only in the .in file, not in the actual script, so that the
# manpage doesn't get rebuilt when building from a tarball.
# Make sure that the qmi-network.1 file is always generated, even when help2man
# is not available
qmi-network.1: $(top_srcdir)/utils/qmi-network.in
	$(AM_V_GEN) \
		$(HELP2MAN) \
			--output=$@ \
			--name='Simple network management of QMI devices' \
			$(top_builddir)/utils/qmi-network || \
		touch $@
