import sys
import application


def main(argv):
    app = application.Application('1280x800')
    app.mainloop()


if __name__ == "__main__":
    main(sys.argv[1:])
