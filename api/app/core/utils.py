import logging

logger = logging.getLogger(__name__)


# TO DO: remove when removing old scielo function
def rtd2(string):
    logger.info("Converting RIS to dictionary ... (2)")
    indict = {}

    lines = string.splitlines()

    for i in lines:
        #print(i)
        spt = i.split('-', 1)
        try:
            one = spt[0].strip()
        except IndexError:
            pass
        if one:
            try:
                two = spt[1].strip()
            except IndexError:
                two = ''
        else:
            pass

        if one and two:
            indict[one] = two
        else:
            pass

    return indict
