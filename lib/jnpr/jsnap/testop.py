import re
import colorama
from collections import defaultdict
import jinja2


class Operator:

    def __init__(self):
        self.result = True
        self.no_failed = 0
        self.no_passed = 0
        self.test_details = defaultdict(list)
        colorama.init(autoreset=True)

    def __del__(self):
        colorama.init(autoreset=True)

    # call methods based on test operation specified, eg if testop is
    # is-equal, then it will call is_equal function
    def define_operator(
            self, testop, x_path, ele_list, err_mssg, info_mssg, teston, iter, id, *args):
        try:
            getattr(
                self,
                testop.replace(
                    '-',
                    '_'))(
                x_path,
                ele_list,
                err_mssg,
                info_mssg,
                teston,
                iter,
                id,
                *args)
        except AttributeError as e:
            print "\nTest Operator not defined !!!!! \nERROR Message :", e.message
            self.no_failed= self.no_failed +1
        except:
            print "\nUndefined error occurred, please check test cases !!!"
            self.no_failed= self.no_failed +1


    def print_result(self, testname, result):
        if result is False:
            self.no_failed = self.no_failed + 1
            print (
                colorama.Fore.RED +
                '\nFinal result of ' + testname + ': FAILED\n')
        elif result is True:
            self.no_passed = self.no_passed + 1
            print (
                colorama.Fore.GREEN +
                '\nFinal result of ' + testname + ': PASSED \n')

    def print_testmssg(self, testname):
        msg = "Performing %s Test Operation" % testname
        testmssg = (80 - len(msg) - 2) / 2 * '*' + \
            msg + (80 - len(msg) - 2) / 2 * '*'
        print (colorama.Fore.BLUE + testmssg)

# two for loops, one for xpath, other for iterating nodes inside xpath, if value is not
# given for comparision, then it will take first value

    def _find_xpath(self, iter, x_path, xml1=None, xml2=None):
        if xml1 is not None:
            pre_nodes = xml1.xpath(x_path)if iter else xml1.xpath(x_path)[0:1]
        else:
            pre_nodes = xml2.xpath(x_path) if iter else xml2.xpath(x_path)[0:1]
        post_nodes = xml2.xpath(x_path) if iter else xml2.xpath(x_path)[0:1]
        return pre_nodes, post_nodes

    def _find_element(self, id_list, iddict, element, pre_node, post_node):
        prenode = pre_node.xpath(element)
        postnode = post_node.xpath(element)
        for j in range(len(id_list)):
            iddict[
                'id_' +
                str(j)] = post_node.xpath(
                id_list[j])[0].text.strip() if post_node.xpath(
                id_list[j]) else None
        return iddict, prenode, postnode

    def _find_value(self, predict, postdict, element, postnode, prenode):
        post_nodevalue = postnode.text.strip()
        pre_nodevalue = prenode.text.strip()
        predict[element.replace('-', '_')] = pre_nodevalue
        postdict[element.replace('-', '_')] = post_nodevalue
        return predict, postdict, post_nodevalue, pre_nodevalue

    # used by no-diff, list-not-less, not-more
    def _get_data(self, id_list, nodes):
        data = {}
        for path in nodes:
            xlist = [path.find(id) for id in id_list]
            val = []
            for values in xlist:
                if values is not None:
                    val.append(values.text)
            data[tuple(val)] = path
        return data

    # for getting any node value
    def _get_nodevalue(
            self, predict, postdict, pre_nodes, post_nodes, x_path, element, mssg):
        mssg = re.findall('{{(.*?)}}', mssg)
        for e in mssg:
            if (e.startswith("post") or e.startswith("Post")):
                val = e[6:-2]
                if val not in [x_path, element]:
                    postdict[val.replace('-', '_')] = post_nodes.findtext(val)

            if (e.startswith("pre") or e.startswith("PRE")):
                val = e[5:-2]
                if val not in [x_path, element]:
                    predict[val.replace('-', '_')] = pre_nodes.findtext(val)
        return predict, postdict

    def exists(self, x_path, ele_list, err_mssg, info_mssg,
               teston, iter, id_list, xml1, xml2):
        self.print_testmssg("exists")
        res = True
        predict = {}
        postdict = {}
        iddict = {}
        tresult = {
            'xpath': x_path,
            'element_list': ele_list,
            'testoperation': "exists"}
        try:
            element = ele_list[0]
        except IndexError as e:
            print "\n Error occurred while accessing test element", e.message
            print "\n Element is not specified for testing"
        else:
            pre_nodes, post_nodes = self._find_xpath(iter, x_path, xml1, xml2)
            if not post_nodes:
                print "Nodes are not present in given Xpath!!"
                res = False
            else:
                for i in range(len(post_nodes)):
                    iddict, postnode, prenode = self._find_element(
                        id_list, iddict, element, pre_nodes[i], post_nodes[i])
                    predict, postdict = self._get_nodevalue(
                        predict, postdict, pre_nodes[i], post_nodes[i], x_path, element, err_mssg)
                    predict, postdict = self._get_nodevalue(
                        predict, postdict, pre_nodes[i], post_nodes[i], x_path, element, info_mssg)
                    if postnode:
                        for k in range(len(postnode)):
                            predict, postdict, post_nodevalue, pre_nodevalue = self._find_value(
                                predict, postdict, element, postnode[k], prenode[k])
                            print jinja2.Template(info_mssg.replace('-', '_')).render(iddict, pre=predict, post=postdict)
                    else:
                        res = False
                        print jinja2.Template(err_mssg.replace('-', '_')).render(iddict, pre=predict, post=postdict)
        self.print_result('exists', res)
        tresult['result'] = res
        self.test_details[teston].append(tresult)

    def not_exists(self, x_path, ele_list, err_mssg, info_mssg,
                   teston, iter, id_list, xml1, xml2):
        self.print_testmssg("not-exists")
        colorama.init(autoreset=True)
        res = True
        iddict = {}
        predict = {}
        postdict = {}
        tresult = {
            'xpath': x_path,
            'element_list': ele_list,
            'testoperation': "is-equal"}
        try:
            element = ele_list[0]
        except IndexError as e:
            print "\n Error occurred while accessing test element", e.message
            print "\n 'exists' test operator require two parameters"
        else:
            pre_nodes, post_nodes = self._find_xpath(iter, x_path, xml1, xml2)
            if not post_nodes:
                print "Nodes are not present in given Xpath!!"
                res = False
            else:
                for i in range(len(post_nodes)):
                    iddict, postnode, prenode = self._find_element(
                        id_list, iddict, element, pre_nodes[i], post_nodes[i])
                    predict, postdict = self._get_nodevalue(
                        predict, postdict, pre_nodes[i], post_nodes[i], x_path, element, err_mssg)
                    predict, postdict = self._get_nodevalue(
                        predict, postdict, pre_nodes[i], post_nodes[i], x_path, element, info_mssg)
                    if postnode:
                        res = False
                        print jinja2.Template(err_mssg.replace('-', '_')).render(iddict, pre=predict, post=postdict)
                    else:
                        for k in range(len(postnode)):
                            predict, postdict, post_nodevalue, pre_nodevalue = self._find_value(
                                predict, postdict, element, postnode[k], prenode[k])
                            print jinja2.Template(info_mssg.replace('-', '_')).render(iddict, pre=predict, post=postdict)
        self.print_result('not-exists', res)
        tresult['result'] = res
        self.test_details[teston].append(tresult)

    def all_same(
            self, x_path, ele_list, err_mssg, info_mssg, teston, iter, id_list, xml1, xml2):
        self.print_testmssg("all-same")
        res = True
        iddict = {}
        predict = {}
        postdict = {}
        tresult = {
            'xpath': x_path,
            'element_list': ele_list,
            'testoperation': "all-same"}
        try:
            element = ele_list[0]
        except IndexError as e:
            print "\nError occurred while accessing test element", e.message
        else:
            pre_nodes, post_nodes = self._find_xpath(iter, x_path, xml1, xml2)
            if not post_nodes:
                print "Nodes are not present in given Xpath!!"
                res = False
            else:
                if len(ele_list) >= 2:
                    vpath = x_path + ele_list[1] + '/' + ele_list[0]
                    value = xml2.xpath(vpath)[0].text
                else:
                    value = xml2.xpath(x_path + '/' + ele_list[0])[0].text
                for i in range(len(post_nodes)):
                    iddict, postnode, prenode = self._find_element(
                        id_list, iddict, element, pre_nodes[i], post_nodes[i])
                    predict, postdict = self._get_nodevalue(
                        predict, postdict, pre_nodes[i], post_nodes[i], x_path, element, err_mssg)
                    predict, postdict = self._get_nodevalue(
                        predict, postdict, pre_nodes[i], post_nodes[i], x_path, element, info_mssg)
                    if postnode:
                        for k in range(len(postnode)):
                            predict, postdict, post_nodevalue, pre_nodevalue = self._find_value(
                                predict, postdict, element, postnode[k], prenode[k])
                            if post_nodevalue != value.strip():
                                res = False
                                print jinja2.Template(err_mssg.replace('-', '_')).render(iddict, pre=predict, post=postdict)
                            else:
                                print jinja2.Template(info_mssg.replace('-', '_')).render(iddict, pre=predict, post=postdict)

        self.print_result('all-same', res)
        tresult['result'] = res
        self.test_details[teston].append(tresult)

    def is_equal(
            self, x_path, ele_list, err_mssg, info_mssg, teston, iter, id_list, xml1, xml2):
        self.print_testmssg("is-equal")
        res = True
        tresult = {}
        predict = {}
        postdict = {}
        iddict = {}
        tresult['xpath'] = x_path
        tresult['element_list'] = ele_list
        tresult['testoperation'] = "is-equal"
        try:
            element = ele_list[0]
            value = ele_list[1]
        except IndexError as e:
            print "\nError occurred while accessing test element", e.message
            print "\n'is-equal' test operator requires two parameter"
        else:
            pre_nodes, post_nodes = self._find_xpath(iter, x_path, xml1, xml2)
            if not post_nodes:
                print "Nodes are not present in given Xpath!!"
                res = False
            else:
                for i in range(len(post_nodes)):
                    iddict, postnode, prenode = self._find_element(
                        id_list, iddict, element, pre_nodes[i], post_nodes[i])
                    predict, postdict = self._get_nodevalue(
                        predict, postdict, pre_nodes[i], post_nodes[i], x_path, element, err_mssg)
                    predict, postdict = self._get_nodevalue(
                        predict, postdict, pre_nodes[i], post_nodes[i], x_path, element, info_mssg)

                    if postnode:
                        for k in range(len(postnode)):
                            predict, postdict, post_nodevalue, pre_nodevalue = self._find_value(
                                predict, postdict, element, postnode[k], prenode[k])
                            if post_nodevalue == value.strip():
                                print jinja2.Template(info_mssg.replace('-', '_')).render(iddict, pre=predict, post=postdict)
                            else:
                                res = False
                                print jinja2.Template(err_mssg.replace('-', '_')).render(iddict, pre=predict, post=postdict)
        self.print_result('is-equal', res)
        tresult['result'] = res
        self.test_details[teston].append(tresult)

    def not_equal(
            self, x_path, ele_list, err_mssg, info_mssg, teston, iter, id_list, xml1, xml2):
        self.print_testmssg("not-equal")
        res = True
        tresult = {}
        predict = {}
        postdict = {}
        iddict = {}
        tresult['xpath'] = x_path
        tresult['element_list'] = ele_list
        tresult['testoperation'] = "not-equal"
        try:
            element = ele_list[0]
            value = ele_list[1]
        except IndexError as e:
            print "\nError occurred while accessing test element", e.message
            print "\n'not-equal' test operator requires two parameter"
        else:
            pre_nodes, post_nodes = self._find_xpath(iter, x_path, xml1, xml2)
            if not post_nodes:
                print "Nodes are not present in given Xpath!!"
                res = False
            else:
                for i in range(len(post_nodes)):
                    iddict, postnode, prenode = self._find_element(
                        id_list, iddict, element, pre_nodes[i], post_nodes[i])
                    predict, postdict = self._get_nodevalue(
                        predict, postdict, pre_nodes[i], post_nodes[i], x_path, element, err_mssg)
                    predict, postdict = self._get_nodevalue(
                        predict, postdict, pre_nodes[i], post_nodes[i], x_path, element, info_mssg)
                    if postnode:
                        for k in range(len(postnode)):
                            predict, postdict, post_nodevalue, pre_nodevalue = self._find_value(
                                predict, postdict, element, postnode[k], prenode[k])
                            if post_nodevalue != value.strip():
                                print jinja2.Template(info_mssg.replace('-', '_')).render(iddict, pre=predict, post=postdict)
                            else:
                                res = False
                                print jinja2.Template(err_mssg.replace('-', '_')).render(iddict, pre=predict, post=postdict)
        self.print_result('not-equal', res)
        tresult['result'] = res
        self.test_details[teston].append(tresult)

    def in_range(
            self, x_path, ele_list, err_mssg, info_mssg, teston, iter, id_list, xml1, xml2):
        self.print_testmssg("in-range")
        res = True
        iddict = {}
        predict = {}
        postdict = {}
        tresult = {
            'xpath': x_path,
            'element_list': ele_list,
            'testoperation': "in-range"}
        try:
            element = ele_list[0]
            range1 = float(ele_list[1])
            range2 = float(ele_list[2])
        except IndexError as e:
            print "\nError occurred while accessing test element\n", e.message
            print "\n'in-range' test operator requires two parameter"
        else:
            pre_nodes, post_nodes = self._find_xpath(iter, x_path, xml1, xml2)
            if not post_nodes:
                print "Nodes are not present in given Xpath!!"
                res = False
            else:
                for i in range(len(post_nodes)):
                    iddict, postnode, prenode = self._find_element(
                        id_list, iddict, element, pre_nodes[i], post_nodes[i])
                    predict, postdict = self._get_nodevalue(
                        predict, postdict, pre_nodes[i], post_nodes[i], x_path, element, err_mssg)
                    predict, postdict = self._get_nodevalue(
                        predict, postdict, pre_nodes[i], post_nodes[i], x_path, element, info_mssg)

                    if postnode:
                        for k in range(len(postnode)):
                            predict, postdict, post_nodevalue, pre_nodevalue = self._find_value(
                                predict, postdict, element, postnode[k], prenode[k])
                            if (float(post_nodevalue) >= range1
                                    and float(post_nodevalue) <= range2):
                                print jinja2.Template(info_mssg.replace('-', '_')).render(iddict, pre=predict, post=postdict)
                            else:
                                res = False
                                print jinja2.Template(err_mssg.replace('-', '_')).render(iddict, pre=predict, post=postdict)
        self.print_result('in-range', res)
        tresult['result'] = res
        self.test_details[teston].append(tresult)

    def not_range(
            self, x_path, ele_list, err_mssg, info_mssg, teston, iter, id_list, xml1, xml2):
        self.print_testmssg("not-range")
        res = True
        iddict = {}
        predict = {}
        postdict = {}
        tresult = {
            'xpath': x_path,
            'element_list': ele_list,
            'testoperation': "not-range"}
        try:
            element = ele_list[0]
            range1 = float(ele_list[1])
            range2 = float(ele_list[2])
        except IndexError as e:
            print "\n Error occurred while accessing test element", e.message
            print "\n not-range test operator require two parameters"
        else:
            pre_nodes, post_nodes = self._find_xpath(iter, x_path, xml1, xml2)
            if not post_nodes:
                print "Nodes are not present in given Xpath!!"
                res = False
            else:
                for i in range(len(post_nodes)):
                    iddict, postnode, prenode = self._find_element(
                        id_list, iddict, element, pre_nodes[i], post_nodes[i])
                    predict, postdict = self._get_nodevalue(
                        predict, postdict, pre_nodes[i], post_nodes[i], x_path, element, err_mssg)
                    predict, postdict = self._get_nodevalue(
                        predict, postdict, pre_nodes[i], post_nodes[i], x_path, element, info_mssg)
                    if postnode:
                        for k in range(len(postnode)):
                            predict, postdict, post_nodevalue, pre_nodevalue = self._find_value(
                                predict, postdict, element, postnode[k], prenode[k])

                            if float(post_nodevalue) <= range1 and float(
                                    post_nodevalue) >= range2:
                                print jinja2.Template(info_mssg.replace('-', '_')).render(iddict, pre=predict, post=postdict)
                            else:
                                res = False
                                print jinja2.Template(err_mssg.replace('-', '_')).render(iddict, pre=predict, post=postdict)
        self.print_result('not-range', res)
        tresult['result'] = res
        self.test_details[teston].append(tresult)

    def is_gt(self, x_path, ele_list, err_mssg,
              info_mssg, teston, iter, id_list, xml1, xml2):
        self.print_testmssg("is-gt")
        res = True
        iddict = {}
        predict = {}
        postdict = {}
        tresult = {
            'xpath': x_path,
            'element_list': ele_list,
            'testoperation': "is-gt"}
        try:
            element = ele_list[0]
            val1 = float(ele_list[1])
        except IndexError as e:
            print "\nError occurred while accessing test element", e.message
            print "\n'is-gt' test operator require two parameters"
        else:
            pre_nodes, post_nodes = self._find_xpath(iter, x_path, xml1, xml2)
            if not post_nodes:
                print "Nodes are not present in given Xpath!!"
                res = False
            else:
                for i in range(len(post_nodes)):
                    iddict, postnode, prenode = self._find_element(
                        id_list, iddict, element, pre_nodes[i], post_nodes[i])
                    predict, postdict = self._get_nodevalue(
                        predict, postdict, pre_nodes[i], post_nodes[i], x_path, element, err_mssg)
                    predict, postdict = self._get_nodevalue(
                        predict, postdict, pre_nodes[i], post_nodes[i], x_path, element, info_mssg)

                    if postnode:
                        for j in range(len(postnode)):
                            predict, postdict, post_nodevalue, pre_nodevalue = self._find_value(
                                predict, postdict, element, postnode[j], prenode[j])
                            if (float(post_nodevalue) > val1):
                                print jinja2.Template(info_mssg.replace('-', '_')).render(iddict, pre=predict, post=postdict)
                            else:
                                res = False
                                print jinja2.Template(err_mssg.replace('-', '_')).render(iddict, pre=predict, post=postdict)
        self.print_result('is-gt', res)
        tresult['result'] = res
        self.test_details[teston].append(tresult)

    def is_lt(self, x_path, ele_list, err_mssg,
              info_mssg, teston, iter, id_list, xml1, xml2):
        self.print_testmssg("is-lt")
        res = True
        iddict = {}
        predict = {}
        postdict = {}
        tresult = {
            'xpath': x_path,
            'element_list': ele_list,
            'testoperation': "is-lt"}
        try:
            element = ele_list[0]
            val1 = float(ele_list[1])
        except IndexError as e:
            print "\nError occurred while accessing test element ", e.message
            print "\n'is-lt' test operator require two parameters"
        else:
            pre_nodes, post_nodes = self._find_xpath(iter, x_path, xml1, xml2)

            if not post_nodes:
                print "Nodes are not present in given Xpath!!"
                res = False
            else:
                for i in range(len(post_nodes)):
                    iddict, postnode, prenode = self._find_element(
                        id_list, iddict, element, pre_nodes[i], post_nodes[i])
                    predict, postdict = self._get_nodevalue(
                        predict, postdict, pre_nodes[i], post_nodes[i], x_path, element, err_mssg)
                    predict, postdict = self._get_nodevalue(
                        predict, postdict, pre_nodes[i], post_nodes[i], x_path, element, info_mssg)

                    if postnode:
                        for k in range(len(postnode)):
                            predict, postdict, post_nodevalue, pre_nodevalue = self._find_value(
                                predict, postdict, element, postnode[k], prenode[k])
                            if (float(post_nodevalue) < val1):
                                print jinja2.Template(info_mssg.replace('-', '_')).render(iddict, pre=predict, post=postdict)
                            else:
                                res = False
                                print jinja2.Template(err_mssg.replace('-', '_')).render(iddict, pre=predict, post=postdict)
        self.print_result('is-lt', res)
        tresult['result'] = res
        self.test_details[teston].append(tresult)

    def contains(
            self, x_path, ele_list, err_mssg, info_mssg, teston, iter, id_list, xml1, xml2):
        self.print_testmssg("contains")
        predict = {}
        postdict = {}
        iddict = {}
        res = True
        tresult = {
            'xpath': x_path,
            'element_list': ele_list,
            'testoperation': "contains"}
        try:
            element = ele_list[0]
            value = ele_list[1]
        except IndexError as e:
            print "\nError occurred while accessing test element", e.message
            print "\n'contains' require two parameters"
        else:
            pre_nodes, post_nodes = self._find_xpath(iter, x_path, xml1, xml2)
            if not post_nodes:
                print "Nodes are not present in given Xpath!!"
                res = False
            else:
                for i in range(len(post_nodes)):
                    Operator.iddict, postnode, prenode = self._find_element(
                        id_list, iddict, element, pre_nodes[i], post_nodes[i])
                    predict, postdict = self._get_nodevalue(
                        predict, postdict, pre_nodes[i], post_nodes[i], x_path, element, err_mssg)
                    predict, postdict = self._get_nodevalue(
                        predict, postdict, pre_nodes[i], post_nodes[i], x_path, element, info_mssg)
                    if postnode:
                        for k in range(len(postnode)):
                            predict[
                                (element.replace('-', '_'))] = prenode[k].text
                            postdict[
                                (element.replace('-', '_'))] = postnode[k].text
                            if (postnode[k].text.find(value) == -1):
                                res = False
                                print jinja2.Template(err_mssg.replace('-', '_')).render(iddict, pre=predict, post=postdict)
                            else:
                                print jinja2.Template(info_mssg.replace('-', '_')).render(iddict, pre=predict, post=postdict)
                    else:
                        print "Error!!, Node is not present in path given with test operator!!"
                        res = False
        self.print_result('contains', res)
        tresult['result'] = res
        self.test_details[teston].append(tresult)

    def is_in(self, x_path, ele_list, err_mssg,
              info_mssg, teston, iter, id_list, xml1, xml2):
        self.print_testmssg("is-in")
        res = True
        iddict = {}
        predict = {}
        postdict = {}
        tresult = {
            'xpath': x_path,
            'element_list': ele_list,
            'testoperation': "is-in"}
        try:
            element = ele_list[0]
            value_list = ele_list[1:]
        except IndexError as e:
            print "\nError occurred while accessing test element", e.message
            print "\n'is-in' test operator require two parameters"
        else:
            pre_nodes, post_nodes = self._find_xpath(iter, x_path, xml1, xml2)
            if not post_nodes:
                print "Nodes are not present in given Xpath!!"
                res = False
            else:
                for i in range(len(post_nodes)):
                    iddict, postnode, prenode = self._find_element(
                        id_list, iddict, element, pre_nodes[i], post_nodes[i])
                    predict, postdict = self._get_nodevalue(
                        predict, postdict, pre_nodes[i], post_nodes[i], x_path, element, err_mssg)
                    predict, postdict = self._get_nodevalue(
                        predict, postdict, pre_nodes[i], post_nodes[i], x_path, element, info_mssg)
                    if postnode:
                        for k in range(len(postnode)):
                            predict, postdict, post_nodevalue, pre_nodevalue = self._find_value(
                                predict, postdict, element, postnode[k], prenode[k])
                            if (post_nodevalue in value_list):
                                print jinja2.Template(info_mssg.replace('-', '_')).render(iddict, pre=predict, post=postdict)
                            else:
                                res = False
                                print jinja2.Template(err_mssg.replace('-', '_')).render(iddict, pre=predict, post=postdict)
        self.print_result('is-in', res)
        tresult['result'] = res
        self.test_details[teston].append(tresult)

    def not_in(self, x_path, ele_list, err_mssg,
               info_mssg, teston, iter, id_list, xml1, xml2):
        self.print_testmssg("not-in")
        res = True
        iddict = {}
        predict = {}
        postdict = {}
        tresult = {
            'xpath': x_path,
            'element_list': ele_list,
            'testoperation': "not-in"}
        try:
            element = ele_list[0]
            value_list = ele_list[1:]
        except IndexError as e:
            print "\nError occurred while accessing test element", e.message
            print "\n'not-in' test operator require two parameters"
        else:
            pre_nodes, post_nodes = self._find_xpath(iter, x_path, xml1, xml2)
            if not post_nodes:
                print "Nodes are not present in given Xpath!!"
                res = False
            else:
                for i in range(len(post_nodes)):
                    iddict, postnode, prenode = self._find_element(
                        id_list, iddict, element, pre_nodes[i], post_nodes[i])
                    predict, postdict = self._get_nodevalue(
                        predict, postdict, pre_nodes[i], post_nodes[i], x_path, element, err_mssg)
                    predict, postdict = self._get_nodevalue(
                        predict, postdict, pre_nodes[i], post_nodes[i], x_path, element, info_mssg)
                    if postnode:
                        for k in range(len(postnode)):
                            predict, postdict, post_nodevalue, pre_nodevalue = self._find_value(
                                predict, postdict, element, postnode[k], prenode[k])
                            if (post_nodevalue not in value_list):
                                print jinja2.Template(info_mssg.replace('-', '_')).render(iddict, pre=predict, post=postdict)
                            else:
                                res = False
                                print jinja2.Template(err_mssg.replace('-', '_')).render(iddict, pre=predict, post=postdict)
        self.print_result('not-in', res)
        tresult['result'] = res
        self.test_details[teston].append(tresult)

    # operator requiring two operands
    def no_diff(self, x_path, ele_list, err_mssg,
                info_mssg, teston, iter, id_list, xml1, xml2):

        self.print_testmssg("no-diff")
        res = True
        iddict = {}
        predict = {}
        postdict = {}
        tresult = {
            'xpath': x_path,
            'element_list': ele_list,
            'testoperation': "no-diff"}
        pre_nodes, post_nodes = self._find_xpath(iter, x_path, xml1, xml2)

        if (not pre_nodes) or (not post_nodes):
            print "Nodes are not present in given Xpath!!"
            res = False

        else:
            # assuming one iterator has unique set of ids, i.e only one node matching to id
            # making dictionary for id and its corresponding xpath
            predata = self._get_data(id_list, pre_nodes)
            postdata = self._get_data(id_list, post_nodes)

            if len(predata.keys()) >= len(postdata.keys()):
                data1 = predata
                data2 = postdata
            else:
                data1 = postdata
                data2 = predata

            for k in data1:
                for length in range(len(k)):
                    iddict['id_' + str(length)] = k[length].strip()

                if k in data2:
                    predict, postdict = self._get_nodevalue(
                        predict, postdict, data1[k], data2[k], x_path, ele_list[0], err_mssg)
                    predict, postdict = self._get_nodevalue(
                        predict, postdict, data1[k], data2[k], x_path, ele_list[0], info_mssg)

                    ele_xpath1 = data1.get(k).xpath(ele_list[0])
                    ele_xpath2 = data2.get(k).xpath(ele_list[0])
                    # assuming only one node
                    val_list1 = [
                        element.text for element in ele_xpath1][0].strip()
                    val_list2 = [
                        element.text for element in ele_xpath2][0].strip()
                    predict[ele_list[0].replace('-', '_')] = val_list1
                    postdict[ele_list[0].replace('-', '_')] = val_list2
                    if val_list1 != val_list2:
                        res = False
                        print jinja2.Template(err_mssg.replace('-', '_')).render(iddict, pre=predict, post=postdict)
                    else:
                        print jinja2.Template(info_mssg.replace('-', '_')).render(iddict, pre=predict, post=postdict)
                else:
                    print "\nError, id miss match ocuurred!!"
                    for kval in k:
                        print "Missing node:", kval.strip()
                    res = False
        self.print_result('no-diff', res)
        tresult['result'] = res
        self.test_details[teston].append(tresult)

    def list_not_less(
            self, x_path, ele_list, err_mssg, info_mssg, teston, iter, id_list, xml1, xml2):
        self.print_testmssg("list-not-less")
        res = True
        tresult = {
            'xpath': x_path,
            'element_list': ele_list,
            'testoperation': "list-not-less"}
        iddict = {}
        predict = {}
        postdict = {}
        pre_nodes, post_nodes = self._find_xpath(iter, x_path, xml1, xml2)

        if not pre_nodes or not post_nodes:
            print "Nodes are not present in given Xpath!!"
            res = False
        else:
            # assuming one iterator has unique set of ids, i.e only one node matching to id
            # making dictionary for id and its corresponding xpath

            predata = self._get_data(id_list, pre_nodes)
            postdata = self._get_data(id_list, post_nodes)

            for k in predata:
                for length in range(len(k)):
                    iddict['id_' + str(length)] = k[length].strip()
                if k in postdata:

                    predict, postdict = self._get_nodevalue(
                        predict, postdict, predata[k], postdata[k], x_path, ele_list[0], err_mssg)
                    predict, postdict = self._get_nodevalue(
                        predict, postdict, predata[k], postdata[k], x_path, ele_list[0], info_mssg)

                    if ele_list is not None:
                        ele_xpath1 = predata.get(k).xpath(ele_list[0])
                        ele_xpath2 = postdata.get(k).xpath(ele_list[0])
                        val_list1 = [element.text.strip()
                                     for element in ele_xpath1]
                        val_list2 = [element.text.strip()
                                     for element in ele_xpath2]

                        for val1 in val_list1:
                            predict[ele_list[0].replace('-', '_')] = val1
                            if val1 not in val_list2:
                                # user can only ask for values which are in pre
                                # and not in post
                                res = False
                                print "Missing node :", val1, "for element tag ", ele_xpath1[0].tag, \
                                    "and parent element", ele_xpath1[
                                        0].getparent().tag
                                print jinja2.Template(err_mssg.replace('-', '_')).render(iddict, pre=predict, post=postdict)
                            else:
                                print jinja2.Template(info_mssg.replace('-', '_')).render(iddict, pre=predict, post=postdict)
                else:
                    print "\nERROR, id miss match occurred!!!"
                    for kval in k:
                        print "Missing node:", kval.strip()
                    res = False
        self.print_result('list-not-less', res)
        tresult['result'] = res
        self.test_details[teston].append(tresult)

    def list_not_more(
            self, x_path, ele_list, err_mssg, info_mssg, teston, iter, id_list, xml1, xml2):
        msg = "Performing list-not-more Test Operation"
        self.print_testmssg(msg)
        res = True
        tresult = {
            'xpath': x_path,
            'element_list': ele_list,
            'testoperation': "list-not-more"}
        iddict = {}
        predict = {}
        postdict = {}
        pre_nodes, post_nodes = self._find_xpath(iter, x_path, xml1, xml2)

        if not pre_nodes or not post_nodes:
            print "Nodes are not present in given Xpath!!"
            res = False

        else:
            # assuming one iterator has unique set of ids, i.e only one node matching to id
            # making dictionary for id and its corresponding xpath
            predata = self._get_data(id_list, pre_nodes)
            postdata = self._get_data(id_list, post_nodes)

            for k in postdata:
                for length in range(len(k)):
                    iddict['id_' + str(length)] = k[length].strip()

                if k in predata:

                    predict, postdict = self._get_nodevalue(
                        predict, postdict, predata[k], postdata[k], x_path, ele_list[0], err_mssg)
                    predict, postdict = self._get_nodevalue(
                        predict, postdict, predata[k], postdata[k], x_path, ele_list[0], info_mssg)

                    if ele_list is not None:
                        ele_xpath1 = predata.get(k).xpath(ele_list[0])
                        ele_xpath2 = postdata.get(k).xpath(ele_list[0])
                        val_list1 = [element.text.strip()
                                     for element in ele_xpath1]
                        val_list2 = [element.text.strip()
                                     for element in ele_xpath2]
                        for val2 in val_list2:
                            postdict[ele_list[0].replace('-', '_')] = val2
                            if val2 not in val_list1:
                                res = False
                                print "Missing node :", val2, "for element tag ", ele_xpath2[0].tag, \
                                    "and parent element", ele_xpath2[
                                        0].getparent().tag
                                print predict, postdict
                                print jinja2.Template(err_mssg.replace('-', '_')).render(iddict, pre=predict, post=postdict)
                            else:
                                print jinja2.Template(info_mssg.replace('-', '_')).render(iddict, pre=predict, post=postdict)
                else:
                    print "\nERROR, id miss match occurred !!"
                    for kval in k:
                        print "Missing node:", kval.strip()
                    res = False
        self.print_result('list-not-more', res)
        tresult['result'] = res
        self.test_details[teston].append(tresult)

    def delta(self, x_path, ele_list, err_mssg,
              info_mssg, teston, iter, id_list, xml1, xml2):
        self.print_testmssg("delta")
        res = True
        tresult = {
            'xpath': x_path,
            'element_list': ele_list,
            'testoperation': "delta"}
        iddict = {}
        predict = {}
        postdict = {}
        pre_nodes, post_nodes = self._find_xpath(iter, x_path, xml1, xml2)

        if not pre_nodes or not post_nodes:
            print "Nodes are not present in given Xpath!!"
            res = False

        else:
            # assuming one iterator has unique set of ids, i.e only one node matching to id
            # making dictionary for id and its corresponding xpath

            predata = self._get_data(id_list, pre_nodes)
            postdata = self._get_data(id_list, post_nodes)

            for k in predata:
                # checking if id in first data set is present in second data
                # set or not
                for length in range(len(k)):
                    iddict['id_' + str(length)] = k[length]

                if k in postdata:

                    predict, postdict = self._get_nodevalue(
                        predict, postdict, predata[k], postdata[k], x_path, ele_list[0], err_mssg)
                    predict, postdict = self._get_nodevalue(
                        predict, postdict, predata[k], postdata[k], x_path, ele_list[0], info_mssg)

                    if ele_list is not None:
                        # print "data values are", data1.get(k), data2.get(k)
                        ele_xpath1 = predata.get(k).xpath(ele_list[0])
                        ele_xpath2 = postdata.get(k).xpath(ele_list[0])
                        if len(ele_xpath1) and len(ele_xpath2):
                            val1 = float(
                                ele_xpath1[0].text)  # value of desired node for pre snapshot
                            val2 = float(
                                ele_xpath2[0].text)  # value of desired node for post snapshot
                            del_val = ele_list[1]
                            predict[ele_list[0].replace('-', '_')] = val1
                            postdict[ele_list[0].replace('-', '_')] = val2

                            # for negative percentage
                            if re.search('%', del_val) and (
                                    re.search('-', del_val)):
                                dvalue = abs(float(ele_list[1].strip('%')))
                                mvalue = val1 - ((val1 * dvalue) / 100)
                                if (val2 > val1 or val2 < mvalue):
                                    res = False
                                    print jinja2.Template(err_mssg.replace('-', '_')).render(iddict, pre=predict, post=postdict)
                                else:
                                    print jinja2.Template(info_mssg.replace('-', '_')).render(iddict, pre=predict, post=postdict)

                            # for positive percent change
                            elif re.search('%', del_val) and (re.search('/+', del_val)):
                                dvalue = float(ele_list[1].strip('%'))
                                mvalue = val1 + ((val1 * dvalue) / 100)
                                if (val2 < val1 or val2 > mvalue):
                                    res = False
                                    print jinja2.Template(err_mssg.replace('-', '_')).render(iddict, pre=predict, post=postdict)
                                else:
                                    print jinja2.Template(info_mssg.replace('-', '_')).render(iddict, pre=predict, post=postdict)

                            # absolute percent change
                            elif re.search('%', del_val):
                                dvalue = float(ele_list[1].strip('%'))
                                mvalue1 = val1 - (val1 * dvalue) / 100
                                mvalue2 = val1 + (val1 * dvalue) / 100
                                if (val2 < mvalue1 or val2 > mvalue2):
                                    res = False
                                    print jinja2.Template(err_mssg.replace('-', '_')).render(iddict, pre=predict, post=postdict)
                                else:
                                    print jinja2.Template(info_mssg.replace('-', '_')).render(iddict, pre=predict, post=postdict)

                            # for negative change
                            elif re.search('-', del_val):
                                dvalue = abs(float(ele_list[1].strip('%')))
                                mvalue = val1 - dvalue
                                if (val2 < mvalue or val2 > val1):
                                    res = False
                                    print jinja2.Template(err_mssg.replace('-', '_')).render(iddict, pre=predict, post=postdict)
                                else:
                                    print jinja2.Template(info_mssg.replace('-', '_')).render(iddict, pre=predict, post=postdict)

                             # for positive change
                            elif re.search('\+', del_val):
                                dvalue = float(ele_list[1].strip('%'))
                                mvalue = val1 + dvalue
                                if (val2 >= mvalue or val2 <= val1):
                                    res = False
                                    print jinja2.Template(err_mssg.replace('-', '_')).render(iddict, pre=predict, post=postdict)
                                else:
                                    print jinja2.Template(info_mssg.replace('-', '_')).render(iddict, pre=predict, post=postdict)

                            else:
                                dvalue = float(ele_list[1].strip('%'))
                                mvalue1 = val1 - dvalue
                                mvalue2 = val1 + dvalue
                                if (val2 < mvalue1 or val2 > mvalue2):
                                    res = False
                                    print jinja2.Template(err_mssg.replace('-', '_')).render(iddict, pre=predict, post=postdict)
                                else:
                                    print jinja2.Template(info_mssg.replace('-', '_')).render(iddict, pre=predict, post=postdict)
                else:
                    print "\n ERROR, id miss match occurred !! "
                    for kval in k:
                        print "missing node:", kval.strip()
                    res = False

        self.print_result('delta', res)
        tresult['result'] = res
        self.test_details[teston].append(tresult)

    # generate final result
    def final_result(self):
        msg = " Final Result!! "
        finalmssg = (80 - len(msg) - 2) / 2 * '-' + \
            msg + (80 - len(msg) - 2) / 2 * '-'

        print (colorama.Fore.BLUE + "\n" + finalmssg)
        print (
            colorama.Fore.GREEN +
            "\nTotal No of tests passed: {}".format(
                self.no_passed))
        print (
            colorama.Fore.RED +
            "\nTotal No of tests failed: {} ".format(
                self.no_failed))
        if (self.no_failed):
            print (
                colorama.Fore.RED +
                colorama.Style.BRIGHT +
                "\nOverall Tests failed!!! ")
            self.result = "Failed"
        elif (self.no_passed == 0 and self.no_failed == 0):
            print (
                colorama.Fore.RED +
                colorama.Style.BRIGHT +
                "\nNone of the test cases executed !!! ")
        else:
            print (
                colorama.Fore.GREEN +
                colorama.Style.BRIGHT +
                "\nOverall Tests passed!!! ")
            self.result = "Passed"
