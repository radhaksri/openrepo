from django.core.management.base import BaseCommand, CommandError
from repo.models import Repository
import time
import logging
from repo.worker.bgworker import BackgroundWorker, ChoreList


logger = logging.getLogger("openrepo_web")

class Command(BaseCommand):
    help = 'Ensures that all PGP keys in database are added to local keychain'

    def add_arguments(self, parser):
        parser.add_argument('-n', '--num_threads', type=int, default=4, required=False,
                            help='Number of simultaneous worker threads to run')

    def handle(self, *args, **options):

        num_threads = options['num_threads']
        if num_threads < 1 or num_threads > 100:
            self.stdout.write(f"Invalid number of threads ({num_threads})")
            return

        chores = ChoreList()
        threads = []
        for i in range(0, num_threads):
            worker = BackgroundWorker(chores)
            worker.start()
            threads.append(worker)


        while True:
            try:
                time.sleep(1.0)

                stale_repos = Repository.objects.filter(is_stale=True)


                logger.debug(f"{len(stale_repos)} stale repos")

                for repo in stale_repos:
                    chores.set_needs_clean(repo.repo_uid)

            except KeyboardInterrupt:
                break
            except:
                logger.exception("Unhandled exception processing worker thread")

        logger.info("Exiting worker thread")
        # end the threads
        for t in threads:
            t.stop()
        for t in threads:
            t.join()


        self.stdout.write(self.style.SUCCESS('Worker exited'))